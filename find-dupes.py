
import sys

from dupes.cache import Cache


def main():
    """
    Actually try and find duplicates.
    """
    db_path = './files.db'
    c = Cache(db_path)
    duplicates = c.calculate_duplicates()

    total_count = 0
    total_bytes = 0
    redundant_count = 0
    redundant_bytes = 0
    for sha256 in duplicates:
        files = duplicates[sha256]
        for count, f in enumerate(files):
            total_count += 1
            total_bytes += f.size

            if (f.path).startswith('/srv/library'):
                if count > 0:
                    print("    {}".format(f.path))
                    redundant_count += 1
                    redundant_bytes += f.size
                else:
                    print(f.path)

    print("{:,} duplicated files".format(total_count))
    print("{:,} duplicated bytes".format(total_bytes))
    print()
    print("{:,} redundant files".format(redundant_count))
    print("{:,} redundant bytes".format(redundant_bytes))


if __name__ == '__main__':
    if len(sys.argv) != 1:
        print("Examine duplicate files within database")
        print("usage: {}".format(sys.argv[0]))
        sys.exit(1)
    else:
        main()
