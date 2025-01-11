import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io
from matplotlib.dates import HourLocator, DateFormatter


class GymStats:
    def __init__(self, stats_file="stats.csv"):
        """Initialize GymStats with the path to the stats CSV file."""
        self.stats_file = stats_file
        self.club_name = "Wrocław_Ferio_Gaj"

    def _load_data(self):
        """Load and prepare the data from CSV file."""
        df = pd.read_csv(self.stats_file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        # Set timestamp as index for time series operations
        df.set_index("timestamp", inplace=True)
        return df

    def _resample_data(self, df, interval="20min"):
        """
        Resample data to regular intervals using mean for aggregation.
        Handles missing data points gracefully.
        """
        return df[self.club_name].resample(interval).mean()

    def get_current_members(self):
        """Get the current number of members in the club."""
        df = self._load_data()
        return df[self.club_name].iloc[-1]

    def get_max_members(self, days=1):
        """Get maximum number of members in the last N days."""
        df = self._load_data()
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_data = df[df.index > cutoff_time]
        return recent_data[self.club_name].max()

    def create_time_series_plot(self, hours=24, interval="20min"):
        """
        Create a time series plot of members in the club.

        Args:
            hours (int): Number of hours of history to show
            interval (str): Resampling interval ('10min' or '20min')
        """
        df = self._load_data()

        # Filter recent data
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = df[df.index > cutoff_time].copy()

        # Resample data to regular intervals
        resampled_data = self._resample_data(recent_data, interval)

        # Create figure
        plt.figure(figsize=(15, 7))

        # Plot the data
        plt.plot(
            resampled_data.index,
            resampled_data.values,
            marker="o",
            linestyle="-",
            linewidth=2,
            markersize=4,
        )

        # Customize the plot
        plt.title(f"Members Count Over Time - Last {hours}h\n{self.club_name}")
        plt.xlabel("Time")
        plt.ylabel("Number of Members")
        plt.grid(True, alpha=0.3)

        # Format x-axis
        plt.gca().xaxis.set_major_locator(HourLocator(interval=2))
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M"))

        # Rotate and align the tick labels so they look better
        plt.gcf().autofmt_xdate()

        # Add current time marker
        plt.axvline(
            x=datetime.now(), color="r", linestyle="--", alpha=0.5, label="Current Time"
        )
        plt.legend()

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        plt.close()
        buf.seek(0)
        return buf

    def get_stats_summary(self):
        """Get a summary of all stats."""
        current = self.get_current_members()
        max_24h = self.get_max_members(days=1)
        max_7d = self.get_max_members(days=7)
        max_14d = self.get_max_members(days=14)

        return {
            "current_members": int(current),
            "max_24h": int(max_24h),
            "max_7d": int(max_7d),
            "max_14d": int(max_14d),
        }
