# Queue Simulator

A Python simulation of a processing queue system. People are generated each tick, assigned to available slots, and processed over time. When slots fill up, people wait in a queue and are promoted automatically when space becomes available.

## Features

- Configurable registry limit, processing times, and tick intervals
- Automatic queue promotion when slots free up
- Detailed per-tick logging with totals
- Names and surnames loaded from config file
- Graceful shutdown on `Ctrl+C` with final summary

## Project Structure

```python
queue-simulator/
├── person_registry.py   # Main application
├── config.yaml          # Configuration file
├── requirements.txt     # Dependencies
└── .gitignore
```

## Installation

```bash
git clone https://github.com/yourusername/queue-simulator.git
cd queue-simulator

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp config.example.yaml config.yaml
```

## Configuration

Edit `config.yaml` to adjust simulation parameters:

```yaml
registry:
  limit: 10                  # Max people being processed at once

generator:
  min_user_per_tick: 1       # Min new people per tick
  max_user_per_tick: 5       # Max new people per tick
  min_processing_time: 1     # Min ticks to process one person
  max_processing_time: 4     # Max ticks to process one person
  names:
    - Anna
    - Piotr
  surnames:
    - Nowak
    - Kowalski

pipeline:
  tick_interval: 100         # Total number of ticks to run
  tick_time_interval: 1      # Seconds between ticks
file:
  output: "registry.csv".    # Output File with Result
```

## Usage

```bash
python person_registry.py
```

Example output:

```python
INFO:__main__:Users Added: 3 | Users Finished: 2 | Users Assigned: 8/10 | Users Awaiting: 0 | Users Completed total: 14
INFO:__main__:Simulation finished. Total completed: 87
```

## How It Works

Each tick the simulation:

1. Decrements processing time for all assigned people
2. Removes people who have finished processing
3. Promotes waiting people from the queue to fill empty slots
4. Generates and adds new people
5. Logs the current state

## Requirements

- Python 3.10+
- pyyaml==6.0.3
