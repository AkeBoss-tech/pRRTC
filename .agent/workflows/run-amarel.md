---
description: How to run pRRTC on Rutgers Amarel cluster
---

# pRRTC on Amarel Quick Reference

## 1. Connect to Amarel
```bash
ssh YOUR_NETID@amarel.rutgers.edu
```

## 2. Request GPU Node (Interactive)
```bash
srun -p gpu --gres=gpu:1 --time=02:00:00 --pty bash
```

## 3. Load Modules
```bash
module purge && module load cuda/12.4 cmake eigen/3.4.0 gcc/11
```

## 4. Build (first time only)
```bash
cd ~/pRRTC
cmake -B build -DCMAKE_CUDA_ARCHITECTURES=80
cmake --build build -j4
mkdir -p test_output
```

## 5. Run Benchmark
```bash
./build/evaluate_mbm Panda "my_experiment"
```

## 6. Submit Batch Job (for overnight runs)
```bash
sbatch amarel_job.sh Panda overnight_test
```

## 7. Check Job Status
```bash
squeue -u $USER
```

## 8. View Results
```bash
cat test_output/panda_my_experiment.csv
```
