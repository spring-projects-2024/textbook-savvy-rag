import argparse

from scripts.vector_database.utils import train_vector_db

INPUT_DIR_DEFAULT = "scripts/embeddings/data/"
OUTPUT_FILE_DEFAULT = "scripts/vector_database/data/default.index"
M = 128
CENTROIDS = 10_000
INDEX_DEFAULT = f"IVF{CENTROIDS},PQ{M}x4fsr"
TRAINING_SIZE_DEFAULT = 0.1
NPROBE_DEFAULT = 10
TRAIN_ON_GPU_DEFAULT = False
DEVICE = "cpu"
INPUT_FILE_REGEX = "embeddings_[a-z]+.pt"


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_dir",
        type=str,
        default=INPUT_DIR_DEFAULT,
        help="Location of the directory where the embedding files are located",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE_DEFAULT,
        help="Location where to store the index file",
    )
    parser.add_argument(
        "--index",
        type=str,
        default=INDEX_DEFAULT,
        help="String representing the index that needs to be built",
    )
    parser.add_argument(
        "--training_size",
        type=float,
        default=TRAINING_SIZE_DEFAULT,
        help="Percentage of chunks to use for training",
    )
    parser.add_argument(
        "--nprobe",
        type=int,
        default=NPROBE_DEFAULT,
        help="Number of probes for the IVF quantizer",
    )
    parser.add_argument(
        "--train_on_gpu",
        type=bool,
        default=TRAIN_ON_GPU_DEFAULT,
        help="Whether to train on GPU",
    )

    args = parser.parse_args()

    vector_db = train_vector_db(
        index_str=args.index,
        input_dir=args.input_dir,
        training_size=args.training_size,
        train_on_gpu=args.train_on_gpu,
        nprobe=args.nprobe,
        device=DEVICE,
    )

    vector_db.save_to_disk(args.output)


if __name__ == "__main__":
    main()
