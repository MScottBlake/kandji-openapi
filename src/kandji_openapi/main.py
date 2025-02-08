import argparse
from pathlib import Path

from models.postman_collection import PostmanCollection
from openapi_generator import OpenAPIGenerator
from parser import PostmanParser


def parse_postman_collection(collection_path: Path) -> PostmanCollection:
    """Parse the Postman collection from the given path."""
    return PostmanParser.from_file(str(collection_path)).parse()


def generate_openapi_spec(
    collection: PostmanCollection, output_json: Path, output_yaml: Path
) -> None:
    """Generate OpenAPI specification from the parsed collection."""
    generator = OpenAPIGenerator(collection)
    if generator.validate_spec():
        generator.to_json(output_json)
        generator.to_yaml(output_yaml)
        print(
            f"Successfully converted {collection} to OpenAPI specification.\n\n"
            f"JSON file created: {output_json}\n"
            f"YAML file created: {output_yaml}"
        )


def main(collection_path: Path, output_json: Path, output_yaml: Path) -> None:
    collection = parse_postman_collection(collection_path)
    generate_openapi_spec(collection, output_json, output_yaml)


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Convert Postman collection to OpenAPI 3.1.0"
    )
    arg_parser.add_argument(
        "--collection",
        type=str,
        help="Path to the Postman collection JSON file",
        default="postman_collection.json",
    )
    arg_parser.add_argument(
        "--output-json",
        type=str,
        help="Path to the output OpenAPI JSON file",
        default="openapi.json",
    )
    arg_parser.add_argument(
        "--output-yaml",
        type=str,
        help="Path to the output OpenAPI YAML file",
        default="openapi.yaml",
    )
    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    main(Path(args.collection), Path(args.output_json), Path(args.output_yaml))
