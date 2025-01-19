# Database Schema

## Tables

### 1. gym_stats
Stores the time series data of gym member counts.

```sql
create table gym_stats (
    id bigint generated always as identity primary key,
    timestamp timestamptz not null,
    "Wrocław_Ferio_Gaj" integer
    -- Additional gym columns will be added as needed
);

-- Index for faster timestamp-based queries
create index idx_gym_stats_timestamp on gym_stats(timestamp);
```

### 2. raw_responses
Stores the raw JSON responses from the API for backup purposes.

```sql
create table raw_responses (
    id bigint generated always as identity primary key,
    timestamp timestamptz not null,
    response jsonb not null
);

-- Index for timestamp-based queries
create index idx_raw_responses_timestamp on raw_responses(timestamp);
```

### 3. goals
Stores user fitness goals and progress tracking.

```sql
create table goals (
    id bigint generated always as identity primary key,
    user_id int8 not null,
    user_name text not null,
    target_visits int4 not null,
    current_visits int4 not null,
    created_at timestamptz not null,
    end_date timestamptz not null,
    status text not null
);
```

### 4. bans
Stores user ban records for failed goals.

```sql
create table bans (
    id bigint generated always as identity primary key,
    user_id int8 not null,
    user_name text not null,
    goal_id int8 not null references goals(id),
    ban_date timestamptz not null,
    unban_date timestamptz not null
);
```

## Data Flow

1. The scraper collects data from the WellFitness API every 10 minutes
2. For each data point:
   - The processed stats (timestamp + member counts) are saved to `gym_stats`
   - The complete API response is saved to `raw_responses` as a JSONB backup
3. Users can set fitness goals in the `goals` table
4. If a user fails to meet their goal:
   - The goal status is updated to 'failed'
   - A ban record is created in the `bans` table

## Notes

- Timestamps are stored in UTC (timestamptz)
- The `gym_stats` table uses dynamic columns for each gym location
- The `raw_responses` table stores the complete API response, which can be used for data recovery or analysis if needed
- Goals have statuses: 'active', 'completed', or 'failed'
- Bans are automatically created when a goal is failed and include both ban and unban dates
- There is a foreign key relationship between `bans.goal_id` and `goals.id` 