#!/usr/bin/env python3
"""
Quick analysis script for pRRTC test output.
Analyzes path calculation performance metrics from CSV files.
"""

import csv
import os
from collections import defaultdict

def parse_csv(filepath):
    """Parse a CSV file and return list of dictionaries."""
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys and values
            cleaned = {k.strip(): v.strip() for k, v in row.items()}
            data.append(cleaned)
    return data

def analyze_data(data):
    """Analyze the test data and return statistics."""
    # Group by problem name
    by_problem = defaultdict(list)
    for row in data:
        problem = row.get('problem_name', 'unknown')
        by_problem[problem].append(row)
    
    stats = {}
    
    for problem, rows in by_problem.items():
        # Parse numeric values
        wall_times_ms = []
        kernel_times_ms = []
        costs = []
        path_lengths = []
        iterations = []
        solved_count = 0
        
        for row in rows:
            try:
                wall_ns = float(row.get('wall_ns', 0))
                kernel_ns = float(row.get('kernel_ns', 0))
                cost = float(row.get('cost', 0))
                path_len = int(row.get('path_length', 0))
                iters = int(row.get('iters', 0))
                solved = int(row.get('solved', 0))
                
                wall_times_ms.append(wall_ns / 1_000_000)  # Convert to ms
                kernel_times_ms.append(kernel_ns / 1_000_000)
                costs.append(cost)
                path_lengths.append(path_len)
                iterations.append(iters)
                if solved:
                    solved_count += 1
            except (ValueError, TypeError):
                continue
        
        if wall_times_ms:
            stats[problem] = {
                'count': len(rows),
                'solved': solved_count,
                'success_rate': solved_count / len(rows) * 100,
                'wall_time_ms': {
                    'mean': sum(wall_times_ms) / len(wall_times_ms),
                    'min': min(wall_times_ms),
                    'max': max(wall_times_ms),
                },
                'kernel_time_ms': {
                    'mean': sum(kernel_times_ms) / len(kernel_times_ms),
                    'min': min(kernel_times_ms),
                    'max': max(kernel_times_ms),
                },
                'cost': {
                    'mean': sum(costs) / len(costs),
                    'min': min(costs),
                    'max': max(costs),
                },
                'path_length': {
                    'mean': sum(path_lengths) / len(path_lengths),
                    'min': min(path_lengths),
                    'max': max(path_lengths),
                },
                'iterations': {
                    'mean': sum(iterations) / len(iterations),
                    'min': min(iterations),
                    'max': max(iterations),
                },
            }
    
    return stats

def print_report(stats, filename):
    """Print a formatted report of the statistics."""
    print("=" * 80)
    print(f"pRRTC Performance Analysis: {filename}")
    print("=" * 80)
    
    # Overall summary
    total_problems = sum(s['count'] for s in stats.values())
    total_solved = sum(s['solved'] for s in stats.values())
    all_wall_times = []
    all_kernel_times = []
    
    for s in stats.values():
        all_wall_times.append(s['wall_time_ms']['mean'])
        all_kernel_times.append(s['kernel_time_ms']['mean'])
    
    print(f"\n OVERALL SUMMARY")
    print("-" * 40)
    print(f"Total test cases:    {total_problems}")
    print(f"Total solved:        {total_solved} ({total_solved/total_problems*100:.1f}%)")
    print(f"Avg wall time:       {sum(all_wall_times)/len(all_wall_times):.2f} ms")
    print(f"Avg GPU kernel time: {sum(all_kernel_times)/len(all_kernel_times):.3f} ms")
    print(f"Kernel/Wall ratio:   {sum(all_kernel_times)/sum(all_wall_times)*100:.2f}%")
    
    print(f"\n PER-PROBLEM BREAKDOWN")
    print("-" * 80)
    
    # Sort by problem name
    for problem in sorted(stats.keys()):
        s = stats[problem]
        print(f"\n{problem}")
        print(f"   Tests: {s['count']} | Solved: {s['solved']} ({s['success_rate']:.0f}%)")
        print(f"   Wall Time:   {s['wall_time_ms']['mean']:8.2f} ms  (min: {s['wall_time_ms']['min']:.2f}, max: {s['wall_time_ms']['max']:.2f})")
        print(f"   Kernel Time: {s['kernel_time_ms']['mean']:8.3f} ms  (min: {s['kernel_time_ms']['min']:.3f}, max: {s['kernel_time_ms']['max']:.3f})")
        print(f"   Path Length: {s['path_length']['mean']:8.1f}     (min: {s['path_length']['min']}, max: {s['path_length']['max']})")
        print(f"   Cost:        {s['cost']['mean']:8.2f}     (min: {s['cost']['min']:.2f}, max: {s['cost']['max']:.2f})")
        print(f"   Iterations:  {s['iterations']['mean']:8.1f}     (min: {s['iterations']['min']}, max: {s['iterations']['max']})")
    
    print("\n" + "=" * 80)

def main():
    test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    
    # Find all CSV files
    csv_files = [f for f in os.listdir(test_output_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in test_output directory!")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) in test_output/\n")
    
    for csv_file in sorted(csv_files):
        filepath = os.path.join(test_output_dir, csv_file)
        print(f"Analyzing: {csv_file}")
        
        data = parse_csv(filepath)
        stats = analyze_data(data)
        print_report(stats, csv_file)
        print("\n")

if __name__ == '__main__':
    main()
