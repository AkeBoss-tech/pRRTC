#!/bin/bash
#SBATCH --job-name=pRRTC_benchmark
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=pRRTC_%j.log
#SBATCH --error=pRRTC_%j.err

# ============================================
# pRRTC Benchmark Job for Rutgers Amarel
# ============================================
# Usage: sbatch amarel_job.sh <robot> <experiment_name>
# Example: sbatch amarel_job.sh panda baseline_test
# NOTE: Robot names must be LOWERCASE: panda, fetch, baxter
# ============================================

ROBOT=${1:-panda}
EXPERIMENT=${2:-benchmark_$(date +%Y%m%d_%H%M%S)}

echo "Starting pRRTC benchmark"
echo "Robot: $ROBOT"
echo "Experiment: $EXPERIMENT"
echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"

# Load required modules (tested working on Amarel Jan 2026)
module purge
module load cmake/3.24.3-sw1088
module load cuda/12.1.0
module load gcc/10.3.0-pgarias
module load eigen/3.3.4-gc563

# Navigate to pRRTC directory
cd $SLURM_SUBMIT_DIR

# Build if needed (use -j1 to avoid compiler bus errors)
if [ ! -f "build/evaluate_mbm" ]; then
    echo "Building pRRTC..."
    rm -rf build
    cmake -B build
    cmake --build build -j1
fi

# Create output directory
mkdir -p test_output

# Run benchmark
echo "Running benchmark..."
./build/evaluate_mbm $ROBOT $EXPERIMENT

echo "Benchmark complete"
echo "Results saved to: test_output/${ROBOT}_${EXPERIMENT}.csv"
