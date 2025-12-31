import os
import sys
from typing import Tuple


def parse_blktrace_fields(line: str) -> dict:
    """
    解析单条blktrace记录字段（适配txt格式）
    """
    try:
        # 清理空白字符，合并多空格为单空格
        cleaned_line = ' '.join(line.strip().split())
        parts = cleaned_line.split()
        if len(parts) < 7:  # 至少需要前7个核心字段
            return None

        # 1. 设备主次号（字段1）
        dev_part = parts[0].split(',')
        dev_major = int(dev_part[0]) if dev_part[0].isdigit() else 0
        dev_minor = int(dev_part[1]) if len(dev_part) >= 2 and dev_part[1].isdigit() else 0

        # 2. CPU Core ID（字段2）
        cpu_core = int(parts[1]) if parts[1].isdigit() else 0

        # 3. Record ID（字段3）
        record_id = int(parts[2]) if parts[2].isdigit() else 0

        # 4. 时间戳：秒级浮点数 → 纳秒整数（字段4）
        try:
            timestamp_sec = float(parts[3])
            timestamp_ns = int(timestamp_sec * 1e9)
        except:
            timestamp_ns = 0

        # 5. ProcessID（字段5）
        pid = int(parts[4]) if parts[4].isdigit() else 0

        # 6. Trace Action（字段6）
        trace_action = parts[5].upper() if len(parts) >= 6 else ""

        # 7. OperationType（字段7）
        op_type = parts[6].upper() if len(parts) >= 7 else ""

        # 8. 扇区+大小（字段8及以后，格式：282624 + 8）
        sector_num = int(parts[7])
        sector_size = int(parts[9])

        return {
            "dev_major": dev_major,
            "dev_minor": dev_minor,
            "cpu_core": cpu_core,
            "record_id": record_id,
            "timestamp_ns": timestamp_ns,
            "pid": pid,
            "trace_action": trace_action,
            "op_type": op_type,
            "sector_num": sector_num,
            "sector_size": sector_size,
        }
    except Exception as e:
        return None


def convert_to_mqsim(
        parsed_data: dict,
        mqsim_block_size: int = 512,
        sector_bytes: int = 512
) -> Tuple[bool, str]:
    """
    转换为MQSim格式（仅保留有效I/O记录）
    """
    # 1. 仅保留发起I/O的动作（I）
    if parsed_data["trace_action"] != "I":
        return False, ""

    # 2. 仅保留读/写操作（含RS/WS等复合类型）
    if "R" in parsed_data["op_type"]:
        mqsim_op = 0  # 读（包括R/RS/RW等）
    elif "W" in parsed_data["op_type"]:
        mqsim_op = 1  # 写（包括W/WS等）

    else:
        return False, ""
    print(mqsim_op)
    # 3. 过滤0大小请求
    if parsed_data["sector_size"] <= 0:
        return False, ""

    # 4. 512B逻辑块：LBA=扇区号，块数=扇区数
    mqsim_lba = parsed_data["sector_num"]
    mqsim_block_count = parsed_data["sector_size"]

    # 5. 过滤无效时间戳
    if parsed_data["timestamp_ns"] <= 0:
        return False, ""

    # 6. 发起者ID（设备主次号组合）
    initiator_id = parsed_data["dev_major"] * 1000 + parsed_data["dev_minor"]

    # 7. 构造MQSim行（格式：时间戳 LBA 块数 操作类型 发起者ID）
    mqsim_line = (
        f"{parsed_data['timestamp_ns']} "
        f"{mqsim_lba} "
        f"{mqsim_block_count} "
        f"{mqsim_op} "
        f"{initiator_id}\n"
    )
    print(mqsim_line)
    return True, mqsim_line


def process_txt_ssdtrace(
        input_file: str,
        output_file: str,
        mqsim_block_size: int = 512,
        max_lines: int = None  # 调试用：限制处理行数
):
    """
    处理纯txt格式的ssdtrace文件，转换为MQSim Trace
    :param input_file: 输入txt文件完整路径
    :param output_file: 输出文件完整路径
    :param mqsim_block_size: MQSim逻辑块大小（默认512字节）
    :param max_lines: 最大处理行数（None=处理全部）
    """
    # 检查输入文件
    if not input_file.endswith('.txt'):
        print(f"警告：输入文件 {input_file} 不是.txt格式，仍尝试处理...", file=sys.stderr)
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在！", file=sys.stderr)
        return

    processed_lines = 0
    valid_lines = 0

    # 直接读取txt文件（无需解压）
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f_in, \
            open(output_file, 'w', encoding='utf-8') as f_out:

        print(f"开始处理txt文件：{input_file}")
        print(f"输出文件：{output_file}")
        print("------------------------")

        for line_num, line in enumerate(f_in, 1):
            # 跳过空行
            if not line.strip():
                continue

            # 限制最大处理行数
            if max_lines and processed_lines >= max_lines:
                break

            processed_lines += 1

            # 解析+转换
            parsed_data = parse_blktrace_fields(line)
            if not parsed_data:
                continue

            success, mqsim_line = convert_to_mqsim(parsed_data, mqsim_block_size)
            if success:
                f_out.write(mqsim_line)
                valid_lines += 1

            # 进度打印（每10万行）
            if processed_lines % 100000 == 0:
                print(f"进度：已处理 {processed_lines} 行，有效转换 {valid_lines} 行")

        # 处理完成统计
        print("------------------------")
        print(f"处理完成！")
        print(f"- 总处理行数：{processed_lines}（已跳过空行）")
        print(f"- 有效转换行数：{valid_lines}")
        if os.path.exists(output_file):
            print(f"- 输出文件大小：{os.path.getsize(output_file) / 1024 / 1024:.2f} MB")


# ==================== 主函数（配置txt文件路径） ====================
if __name__ == "__main__":
    # ------------------------
    # 只需修改以下3个参数！
    # ------------------------
    INPUT_FILE = "/Users/wenke.liu/Downloads/lsm-tree/ssdtrace-00"  # 你的txt文件完整路径
    OUTPUT_FILE = "/Users/wenke.liu/Downloads/lsm-tree/modify-ssdtrace-00"   # 输出文件路径
    MAX_LINES = None  # 调试用：设为数字（如10000）仅处理前N行，None=处理全部

    # 执行转换（逻辑块大小512字节）
    process_txt_ssdtrace(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        mqsim_block_size=512,
        max_lines=MAX_LINES
    )