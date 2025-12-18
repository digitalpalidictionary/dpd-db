# -*- coding: utf-8 -*-
import re
import pickle
from pathlib import Path
from urllib.parse import unquote


def parse_single_line(line):
    pattern = r'INFO:\s+(\d+\.\d+\.\d+\.\d+):\d+\s+-\s+"(\w+)\s+([^"]+)\s+HTTP/\d\.\d"\s+(\d+)\s+(.+)'
    match = re.match(pattern, line)

    if match:
        ip, method, path, status_code, status_message = match.groups()

        route = ""
        query = ""
        pattern = r"([^?]+)\?(?:[^=]+)=(.+)"
        match = re.match(pattern, path)
        if match:
            route, query = match.groups()
        query = unquote(query)

        return {
            "ip": ip,
            "method": method,
            "path": path,
            "route": route,
            "query": query,
            "status_code": status_code,
            "status_message": status_message,
        }
    return None


def parse_lines(log_file: Path) -> list[dict]:
    parsed_lines = []
    with open(log_file) as f:
        for line in f:
            line = line.rstrip("\n")
            single_line = parse_single_line(line)
            if single_line:
                parsed_lines.append(single_line)
    return parsed_lines


def process_results(results: list[dict]):
    # Count IPs
    ip_counts = {}
    for result in results:
        ip = result["ip"]
        ip_counts[ip] = ip_counts.get(ip, 0) + 1

    # Count paths
    path_counts = {}
    for result in results:
        path = result["path"]
        path_counts[path] = path_counts.get(path, 0) + 1

    # Count status codes
    status_counts = {}
    for result in results:
        status = result["status_code"]
        status_counts[status] = status_counts.get(status, 0) + 1

    # Print summary
    print(f"Total requests: {len(results)}")
    print("\nTop 10 IPs:")
    for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {ip}: {count} requests")

    print("\nTop 10 paths:")
    for path, count in sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]:
        print(f"  {path}: {count} requests")

    print("\nStatus code distribution:")
    for status, count in sorted(
        status_counts.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {status}: {count} requests")


def main():
    current_working_dir = Path.cwd()
    dpd_dir = current_working_dir / "dpd-db"
    log_files = sorted(dpd_dir.glob("*.uvicorn.log"))

    results = []
    for log_file in log_files:
        parsed_lines = parse_lines(log_file)
        results.extend(parsed_lines)

    # process_results(results)
    output_path = current_working_dir / "processed_logs"
    with open(output_path, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
