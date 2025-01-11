from gym_stats import GymStats


def main():
    stats = GymStats()

    # Get and print summary
    summary = stats.get_stats_summary()
    print("\nStats Summary:")
    print(f"Current members: {summary['current_members']}")
    print(f"Max members (24h): {summary['max_24h']}")
    print(f"Max members (7d): {summary['max_7d']}")
    print(f"Max members (14d): {summary['max_14d']}")

    # Create and save time series plot
    print("\nCreating time series plot...")
    # Test both 10 and 20 minute intervals
    for interval in ["10min", "20min"]:
        plot = stats.create_time_series_plot(hours=24, interval=interval)
        with open(f"members_over_time_{interval}.png", "wb") as f:
            f.write(plot.getvalue())
        print(f"Plot saved as 'members_over_time_{interval}.png'")


if __name__ == "__main__":
    main()
