#!/usr/bin/env python3
"""
Script to validate GitHub Actions workflow files.
This ensures the workflow files are valid YAML and follow basic GitHub Actions structure.
"""

import os
import sys
import yaml
from pathlib import Path

def validate_workflow_file(file_path):
    """Validate a GitHub Actions workflow file."""
    print(f"Validating {file_path}...")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    # Try to parse YAML
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"First 10 lines of {file_path}:")
            for i, line in enumerate(content.splitlines()[:10]):
                print(f"{i+1}: {line}")
            
            workflow = yaml.safe_load(content)
            print(f"YAML Keys: {list(workflow.keys()) if workflow else 'None'}")
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {file_path}")
        print(e)
        return False
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return False
    
    # Check required fields
    if not workflow:
        print(f"Error: Empty workflow file {file_path}")
        return False
    
    if 'name' not in workflow:
        print(f"Warning: Workflow in {file_path} has no name")
    
    if 'on' not in workflow:
        print(f"Error: Workflow in {file_path} has no triggers ('on' field)")
        return False
    
    if 'jobs' not in workflow:
        print(f"Error: Workflow in {file_path} has no jobs")
        return False
    
    # Validate jobs
    for job_id, job in workflow['jobs'].items():
        if 'runs-on' not in job:
            print(f"Error: Job '{job_id}' has no 'runs-on' field")
            return False
        
        if 'steps' not in job:
            print(f"Error: Job '{job_id}' has no steps")
            return False
        
        for i, step in enumerate(job['steps']):
            if not step:
                print(f"Error: Empty step #{i+1} in job '{job_id}'")
                return False
            
            if 'uses' not in step and 'run' not in step:
                print(f"Error: Step #{i+1} in job '{job_id}' has neither 'uses' nor 'run'")
                return False
    
    print(f"✓ Workflow file {file_path} is valid")
    return True

def main():
    """Main function to validate all workflow files."""
    workflows_dir = Path('.github/workflows')
    
    if not workflows_dir.exists():
        print(f"Error: Directory {workflows_dir} does not exist")
        return 1
    
    valid = True
    for file_path in workflows_dir.glob('*.yml'):
        if not validate_workflow_file(file_path):
            valid = False
    
    return 0 if valid else 1

if __name__ == '__main__':
    sys.exit(main()) 