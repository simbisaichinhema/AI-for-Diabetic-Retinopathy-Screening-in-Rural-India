# Simulink Workflow Simulation

## Overview

This directory contains Simulink models for simulating the rural DR screening workflow.

## System Model

```
Fundus Camera → Image Acquisition → Quality Gate → AI Processing → Report Generation → Network Transmission → Ophthalmologist Review Queue
```

## Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| images/hour | Screening throughput | 10-50 |
| processing latency | AI processing time | 2-10 seconds |
| bandwidth | Network speed | 1-10 Mbps |
| transmission delay | Report upload time | 1-30 seconds |
| queue length | Waiting cases | 0-100 |
| ophthalmologist capacity | Reviews per hour | 5-20 |
| referral percentage | Cases requiring referral | 15-30% |

## Simulation Scenarios

1. **Low workload**: 10 images/hour, 1 specialist
2. **Normal rural workload**: 25 images/hour, 2 specialists
3. **High workload**: 50 images/hour, 3 specialists
4. **Low bandwidth**: 1 Mbps, increased transmission delay
5. **Limited specialist capacity**: 1 specialist, high workload

## Model Files

- `models/screening_workflow.slx` - Main Simulink model
- `models/workflow_senarios.m` - MATLAB script to run scenarios

## Output Metrics

- Throughput (images/hour)
- Queue length over time
- End-to-end latency
- Specialist utilization
- Review backlog

## How to Run

1. Open `screening_workflow.slx` in Simulink
2. Run `workflow_scenarios.m` to execute all scenarios
3. View results in the MATLAB workspace
