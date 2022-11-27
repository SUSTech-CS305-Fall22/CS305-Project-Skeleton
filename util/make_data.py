import argparse
import os
import math
import hashlib
import pickle
import sys

BT_CHUNK_SIZE = 512*1024  # 512K
SHA1_HASH_SIZE = 20

def chunk_hash(chunk_btyes):
    sha1_hash = hashlib.sha1()
    sha1_hash.update(chunk_btyes)
    return sha1_hash.hexdigest()

def parse_file(file_dir, chunk_num):
    file_size = os.path.getsize(file_dir)
    num_max = math.floor(file_size/BT_CHUNK_SIZE)
    if num_max < chunk_num:
        print(f"Requested {chunk_num} chunks out of max number of chunks: {num_max}, using {num_max} instead of {chunk_num}", file=sys.stderr)
    num = min(num_max, chunk_num)

    data_chunk = []
    data_hash = []

    with open(file_dir, 'rb') as file:
        for i in range(num):
            chunk_byte = file.read(BT_CHUNK_SIZE)
            data_chunk.append(chunk_byte)
            data_hash.append(chunk_hash(chunk_byte))

    with open("master.chunkhash", 'w') as f:
        for j in range(len(data_hash)):
            print(f"{j+1} {data_hash[j]}", file=f)

    return data_chunk, data_hash

def make_data(input_file, output_file, chunk_num, my_index):
    data_chunk, data_hash = parse_file(input_file, chunk_num)
    my_data = dict(zip([data_hash[i-1] for i in my_index], [data_chunk[i-1] for i in my_index]))
    with open(output_file, "wb") as wf:
        pickle.dump(my_data, wf)
    print([data_hash[i-1] for i in my_index])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='The location of the input file.')
    parser.add_argument('output', type=str, help='The location of the output file.')
    parser.add_argument("num", type=int, help='Splitted to how many chunks')
    parser.add_argument('index', type=str, help='index of chunks to be included in the output file')
    args = parser.parse_args()

    my_input = args.input
    my_output = args.output
    my_index = [int(i) for i in args.index.split(",")]
    make_data(my_input, my_output, args.num, my_index)