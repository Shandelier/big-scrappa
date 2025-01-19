import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io
from matplotlib.dates import HourLocator, DateFormatter
import os


class GymStats:
    def __init__(self, data_dir="data", processed_dir="processed"):
        """Initialize GymStats with the path to data directories."""
        self.stats_file = os.path.join(data_dir, "stats.csv")
        self.processed_dir = processed_dir
        self.club_name = "Wrocław_Ferio_Gaj"

        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

    def _load_data(self):
        """Load and prepare the data from CSV file."""
        df = pd.read_csv(self.stats_file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        # Set timestamp as index for time series operations
        df.set_index("timestamp", inplace=True)
        return df

    def _save_plot(self, buf, filename):
        """Save plot to the processed directory."""
        filepath = os.path.join(self.processed_dir, filename)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        return filepath

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

        Returns:
            io.BytesIO: Buffer containing the plot image
        """
        df = self._load_data()

        # Filter recent data
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = df[df.index > cutoff_time].copy()

        # Resample data to regular intervals
        resampled_data = self._resample_data(recent_data, interval)

        # Set style for better looking plots
        plt.style.use("bmh")  # Using a built-in style that gives clean modern look

        # Create figure with higher DPI for better quality
        plt.figure(figsize=(15, 7), dpi=100)

        # Set the background color to white
        plt.rcParams["figure.facecolor"] = "white"
        plt.rcParams["axes.facecolor"] = "white"

        # Add night time shading (21:00-07:00)
        ax = plt.gca()
        xmin, xmax = resampled_data.index.min(), resampled_data.index.max()

        dates = pd.date_range(
            start=xmin.date(), end=xmax.date() + timedelta(days=1), freq="D"
        )
        for date in dates:
            night_start = pd.Timestamp.combine(date, pd.Timestamp("21:00").time())
            next_morning = pd.Timestamp.combine(
                date + timedelta(days=1), pd.Timestamp("07:00").time()
            )

            if night_start >= xmin and night_start <= xmax:
                ax.axvspan(
                    night_start,
                    min(next_morning, xmax),
                    alpha=0.1,
                    color="gray",
                    zorder=1,
                )

        # Plot the data with a nicer style
        plt.plot(
            resampled_data.index,
            resampled_data.values,
            marker="o",
            linestyle="-",
            linewidth=2,
            markersize=4,
            color="#2196F3",  # Material Design Blue
            zorder=3,
            label="Members Count",
        )

        # Customize the plot
        plt.title(
            f"Members Count Over Time - Last {hours}h\n{self.club_name}",
            pad=20,
            fontsize=14,
            fontweight="bold",
        )
        plt.xlabel("Time", fontsize=12)
        plt.ylabel("Number of Members", fontsize=12)

        # Customize grid
        plt.grid(True, alpha=0.2, linestyle="--", zorder=2)

        # Format x-axis
        plt.gca().xaxis.set_major_locator(HourLocator(interval=2))
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M"))

        # Rotate and align the tick labels so they look better
        plt.gcf().autofmt_xdate()

        # Add current time marker
        plt.axvline(
            x=datetime.now(),
            color="#FF5252",  # Material Design Red
            linestyle="--",
            alpha=0.7,
            label="Current Time",
            zorder=4,
        )

        # Customize legend
        plt.legend(loc="upper right", framealpha=0.9, facecolor="white")

        # Set background color and edge color
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color("#CCCCCC")

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(
            buf,
            format="png",
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()
        buf.seek(0)

        return buf

    def save_plot(self, plot_buffer, interval="20min"):
        """
        Save a plot buffer to the processed directory.

        Args:
            plot_buffer (io.BytesIO): Buffer containing the plot image
            interval (str): Interval used for the plot filename

        Returns:
            str: Path to the saved file
        """
        filename = f"members_over_time_{interval}.png"
        return self._save_plot(plot_buffer, filename)

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
