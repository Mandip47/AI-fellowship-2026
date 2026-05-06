import argparse


def main():
    parser = argparse.ArgumentParser(description="A simple argument parser example")
    parser.add_argument(
        "--name", type=str, required=True, help="Your name"
    )  # -- represtents the optional argument
    parser.add_argument("--age", type=int, required=True, help="Your age")

    args = parser.parse_args()

    print(f"Hello, {args.name}! You are {args.age} years old.")


if __name__ == "__main__":
    main()
