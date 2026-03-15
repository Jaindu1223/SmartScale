import argparse
import sys
import os

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path: sys.path.insert(0, current_dir)

# Import our modular commands
from cmd_deploy import execute_deploy
from cmd_monitor import execute_monitor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="⚡ SmartScale MLOps CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command 1: deploy
    deploy_parser = subparsers.add_parser("deploy", help="Profile and deploy a .pth model to AWS")
    deploy_parser.add_argument("file", type=str, help="Path to the .pth model file")

    # Command 2: monitor
    monitor_parser = subparsers.add_parser("monitor", help="Start the live auto-scaling daemon")

    args = parser.parse_args()

    # Route the request
    if args.command == "deploy":
        execute_deploy(args.file)
    elif args.command == "monitor":
        execute_monitor()
    else:
        parser.print_help()