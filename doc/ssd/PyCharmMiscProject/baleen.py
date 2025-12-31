import os
import math
from typing import List, Dict


def convert_to_mqsim(input_file: str, output_file: str, block_size: int = 512):
    """
    将自定义轨迹格式转换为MQSim输入格式
    :param input_file: 原始轨迹文件路径
    :param output_file: MQSim输出文件路径
    :param block_size: MQSim配置的块大小（字节，默认4KB）
    :param time_unit: 原始op_time的单位（ms/μs，默认ms）
    """
    # 仅保留读写操作（过滤其他无效操作）
    valid_ops = {"1", "2", "3", "4", "5", "6"}

    # 存储block_id到LBA基址的映射（保证LBA连续）
    block_id_to_lba: Dict[str, int] = {}
    next_lba = 0  # 下一个可用的LBA基址

    # 打开文件并处理
    with open(input_file, "r", encoding="utf-8") as f_in, \
            open(output_file, "w", encoding="utf-8") as f_out:

        # 遍历每一行轨迹
        for line_num, line in enumerate(f_in, 1):
            # 去除空白字符并按空格分割字段（兼容多空格分隔）
            fields = line.strip().split()
            if len(fields) < 8:
                print(f"警告：第{line_num}行字段数不足，跳过")
                continue

            # 提取核心字段（按你的字段顺序）
            block_id = fields[0]
            io_offset = int(fields[1])+int(block_id)*8*1024*1024
            io_size = int(fields[2])
            op_time = float(fields[3])
            op_time_us = op_time*1000000
            op_name = fields[4]
            # 忽略pipeline、user_namespace、user_name（无用字段）

            # 过滤非读写操作
            if op_name not in valid_ops:
                continue
            if op_name =="1" or op_name =="2" or op_name =="5":
                op_name = "read"
            else:
                op_name = "write"
            # 2. 映射block_id到LBA基址（保证连续）
            if block_id not in block_id_to_lba:
                block_id_to_lba[block_id] = next_lba
                next_lba += math.ceil(io_size / block_size)  # 预留足够LBA空间

            lba_base = block_id_to_lba[block_id]
            # 合并io_offset到最终LBA（按块大小换算）
            lba = lba_base + (io_offset // block_size)

            # 3. I/O大小转换：字节→块数量（向上取整）
            block_count = math.ceil(io_size / block_size)

            # 4. 统一操作类型为大写（MQSim通用格式）
            op_type = "Read" if op_name.lower() == "read" else "Write"

            # 5. 写入MQSim格式（每行：时间戳(us) LBA 块数量 操作类型）
            f_out.write(f"{op_time_us} {lba} {block_count} {op_type}\n")

    print(f"转换完成！")
    print(f"原始文件：{input_file}")
    print(f"MQSim输入文件：{output_file}")
    print(f"映射的block_id数量：{len(block_id_to_lba)}")
    print(f"转换后的I/O请求数：{sum(1 for _ in open(output_file, 'r'))}")


if __name__ == "__main__":
    # ====================== 配置项（根据你的实际情况修改）======================
    INPUT_FILE = "/Users/wenke.liu/Downloads/baleen/201910 3/Region3/full.trace"  # 你的原始轨迹文件路径
    OUTPUT_FILE = "/Users/wenke.liu/Downloads/baleen/201910 3/Region3/MQSIM_full3.trace"  # 生成的MQSim输入文件路径
    BLOCK_SIZE = 512  # MQSim配置的块大小（字节，默认512byte）
    # ==========================================================================

    # 检查原始文件是否存在
    if not os.path.exists(INPUT_FILE):
        print(f"错误：原始文件 {INPUT_FILE} 不存在！")
    else:
        convert_to_mqsim(INPUT_FILE, OUTPUT_FILE, BLOCK_SIZE)
