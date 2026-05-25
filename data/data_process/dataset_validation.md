# Dataset Validation — Traffix.id

## Synthetic Dataset Overview
Dataset synthetic dibuat untuk meniru pola traffic nyata menggunakan simulasi time-series intersection traffic.

## Traffic Variability
- Peak hour ditambahkan.
- Weekend pattern ditambahkan.
- Weather variability ditambahkan.
- Accident simulation ditambahkan.
- Roadwork simulation ditambahkan.
- Event simulation ditambahkan.

## Time-Series Integrity
- Data sudah diurutkan berdasarkan waktu.
- Tidak ada duplicate timestamp-intersection.
- Tidak ada missing value penting.
- Aggregation dilakukan menjadi 1 row per intersection per tick.

## Feature Engineering
- Time features.
- Lag features.
- Rolling features.
- Delta traffic.
- Weather one-hot encoding.
- Multi-horizon forecasting target.
