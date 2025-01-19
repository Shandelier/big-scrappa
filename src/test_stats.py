from gym_stats import GymStats


def main():
    print("Initializing GymStats...")
    stats = GymStats(processed_dir="processed")

    # Get and print summary
    print("\nFetching stats summary...")
    summary = stats.get_stats_summary()
    print("\nStats Summary:")
    print(f"Current members: {summary['current_members']}")
    print(f"Max members (24h): {summary['max_24h']}")
    print(f"Max members (7d): {summary['max_7d']}")
    print(f"Max members (14d): {summary['max_14d']}")

    # Create and save time series plot
    print("\nCreating time series plots...")
    # Test both 10 and 20 minute intervals
    for interval in ["40min", "20min"]:
        print(f"\nGenerating plot for {interval} interval...")
        plot = stats.create_time_series_plot(hours=72, interval=interval)
        print(f"Saving plot...")
        stats.save_plot(plot, interval)
        print(
            f"Plot saved in processed directory as 'members_over_time_{interval}.png'"
        )


if __name__ == "__main__":
    main()
