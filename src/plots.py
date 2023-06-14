import pandas as pd
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from labellines import labelLine, labelLines
import matplotlib.ticker as mticker
import matplotlib

font = {"family": "serif", "weight": "bold", "size": 14}
matplotlib.rc("font", **font)
import matplotlib.dates as mdates
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

data_crs = ccrs.PlateCarree()
import cartopy.feature as cfeature


def plt_cartopy_ibi(ax, labels=True):
    # ax.set_aspect('auto') # The figure will follow the ratio of the figsize
    ax.coastlines()  # Plot the coastlines
    ax.set_xticks([-15, -5, 5], crs=data_crs)  # Set ticks for longitude
    ax.set_yticks([30, 40, 50], crs=data_crs)  # Set ticks for latitude
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)


class Plots:
    def __init__(self, info, show=False):
        general_info = info["GENERAL_INFO"]
        self.model = str(general_info["MODEL"])
        self.reference = str(general_info["REFERENCE"])
        self.year = int(general_info["YEAR"])
        self.date_start = str(general_info["DATE_START"])
        self.periods = int(general_info["PERIODS"])

        PATH_DETECT_FILES = str(general_info["PATH_DETECT_FILES"])
        PATH_TRAJ_FILES = str(general_info["PATH_TRAJ_FILES"])
        PATH_REF_TRACK = str(general_info["PATH_REF_TRACK"])

        # Geographical extend
        self.lon_min = int(general_info["LON_MIN"])
        self.lon_max = int(general_info["LON_MAX"])
        self.lat_min = int(general_info["LAT_MIN"])
        self.lat_max = int(general_info["LAT_MAX"])

        self.dir_plot = str(info["PLOT_INFO"]["PATH_PLOT"])

        self.show = show

    def plot_one_day_adt(self, h, var_adt, a, c):

        fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
        ax.set_extent([self.lon_min, self.lon_max, self.lat_min, self.lat_max])

        AC_x, AC_y = a.effective_contour_longitude, a.effective_contour_latitude
        CC_x, CC_y = c.effective_contour_longitude, c.effective_contour_latitude

        for i in range(len(AC_x)):
            ax.plot(
                AC_x[i, :],
                AC_y[i, :],
                color="k",
                linestyle="-",
                linewidth=1,
                transform=data_crs,
            )
        for i in range(len(CC_y)):
            ax.plot(
                CC_x[i, :],
                CC_y[i, :],
                color="k",
                linestyle=":",
                linewidth=1.5,
                transform=data_crs,
            )

        ax.set_title(self.model)
        im = h.display(ax, var_adt, vmin=-0.15, vmax=0.15)
        plt_cartopy_ibi(ax, labels=False)
        plt.suptitle("Detection Cyclonic (Dotted) & Anticyclonic (Solid)")
        cbar = fig.colorbar(im, ticks=[-0.1, 0, 0.1])
        cbar.ax.set_ylabel("ADT (m) Filtered (500 km)")  # Colorbar label

        # Save or show
        plt.savefig(
            self.dir_plot + self.model + "_Detection.jpeg", bbox_inches="tight", dpi=600
        )

        if self.show:
            plt.show()

    def plot_all_tracks_period(self, at, ct):
        fig, ax = plt.subplots(subplot_kw=dict(projection=data_crs))
        ax.set_extent([self.lon_min, self.lon_max, self.lat_min, self.lat_max])
        at.plot(
            ax,
            ref=-10,
            label="Anticyclonic {nb_tracks} tracks",
            color="r",
            lw=0.9,
            transform=data_crs,
        )
        ct.plot(
            ax,
            ref=-10,
            label="Cyclonic {nb_tracks} tracks",
            color="b",
            lw=0.9,
            transform=data_crs,
        )
        ax.legend()
        ax.set_title("Tracks " + str(self.model) + " " + str(self.year))
        plt_cartopy_ibi(ax, labels=False)
        plt.savefig(
            self.dir_plot + self.model + "_TRACKS_" + str(self.year) + ".jpeg",
            bbox_inches="tight",
            dpi=600,
        )

        if self.show:
            plt.show()

    def plot_number_detection_time_mean(self, NB_EDDIES):
        t_data = pd.date_range(self.date_start, periods=self.periods, freq="D")
        NB_mean = [np.mean(NB_EDDIES)] * len(t_data)

        fig, ax = plt.subplots(figsize=(12, 6))
        # ax = fig.add_axes([.03,.03,.94,.94])
        ax.plot(t_data, NB_EDDIES, color="black")
        ax.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.ylabel("Nb eddy detected")
        ax.plot(t_data, NB_mean, label="Mean", linestyle="--")
        ax.legend()

        plt.savefig(
            self.dir_plot + "NB_EDDIES_" + self.model + "_" + str(self.year) + ".jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_2d_histo(self, at):
        fig, ax = plt.subplots()
        counts, xedges, yedges, im = ax.hist2d(
            at["effective_radius"] / 1000,
            at["amplitude"] * 100,
            bins=200,
            cmap=plt.cm.jet,
            cmin=1,
        )
        ax.set_xlabel("Radius (km)")
        ax.set_ylabel("Amplitude (cm)")

        fig.colorbar(im, ax=ax)
        plt.title(self.model)
        plt.savefig(
            self.dir_plot
            + "HIST2D_AMP_RAD_"
            + self.model
            + "_"
            + str(self.year)
            + ".jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_histo_hits_false(self, radius_AR_hits, radius_AR_misses, radius_AR_falarm):
        bins = np.arange(0, 400, 3)

        plt.subplots(figsize=(6, 4))
        plt.hist(
            radius_AR_hits,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="hits",
            color="green",
        )
        plt.hist(
            radius_AR_misses,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="misses",
            color="red",
        )
        plt.hist(
            radius_AR_falarm,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="false alarm",
            color="orange",
        )

        plt.gca().set(ylim=(0, 4500), xlim=(0, 100), xlabel="Radius (km)")
        plt.legend()
        plt.suptitle(self.model + " Reference " + self.reference)
        plt.savefig(
            self.dir_plot
            + "HIST_MATCHING_"
            + self.model
            + "_"
            + str(self.year)
            + ".jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_pod_far_amplitude(self, POD_AR, FAR_AR):
        bins = np.arange(0, 400, 1)
        plt.subplots(figsize=(10, 4))
        plt.subplot(121)
        plt.step(bins[:-1], POD_AR, color="black", linewidth=2)
        plt.gca().set(
            ylim=(np.nanmin(POD_AR) - 0.2, 1.05),
            ylabel="Probability of Detection",
            xlim=(0, 20),
            xlabel="Amplitude (cm)",
        )
        plt.xticks(np.arange(0, 20, 5))
        plt.grid()

        plt.subplot(122)
        plt.step(bins[:-1], FAR_AR, color="black", linewidth=2)
        plt.gca().set(
            ylim=(0, np.nanmax(FAR_AR) + 0.2),
            ylabel="False Alarm Ratio",
            xlim=(0, 20),
            xlabel="Amplitude (cm)",
        )
        plt.xticks(np.arange(0, 20, 5))

        plt.grid()
        plt.suptitle(self.model + " Reference " + self.reference)
        plt.tight_layout()
        plt.savefig(
            self.dir_plot
            + "POD_FAR_AMP_"
            + self.model
            + "_"
            + str(self.year)
            + ".jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_pod_far_time(self, AR_POD, AR_FAR):
        t_data = pd.date_range(self.date_start, periods=self.periods - 1, freq="D")
        t_data_obs = pd.date_range(self.date_start, periods=self.periods - 1, freq="D")

        fig, axes = plt.subplots(1, 2, figsize=(17, 3))

        axes[0].plot(t_data_obs, AR_POD, color="black")
        axes[0].set_ylim(0, 1)
        axes[0].xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axes[0].set_title("Probability Of Detection")

        axes[1].plot(t_data_obs, AR_FAR, color="black")
        axes[1].set_ylim(0, 1)
        axes[1].xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axes[1].set_title("False Alarm Ratio")

        plt.savefig(
            self.dir_plot
            + "POD_FAR_TEMP_"
            + self.model
            + "_"
            + str(self.year)
            + ".jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def perf_diag(self, SR, AR_POD):
        plt.subplots(figsize=(10, 10))

        i = np.arange(0, 1.1, 0.01)
        CSI = np.arange(0.1, 1, 0.1)
        for c in CSI:
            y = (c * i) / (c * i - c + i)
            indices = np.where(y <= 0.0)
            y = np.delete(y, indices)
            i = np.delete(i, indices)
            plt.plot(i, y, color="k", linewidth=1.8, label=str(np.round(c, 2)))

        xvals = [0.57, 0.62, 0.77, 0.79, 0.85, 0.9, 0.95, 0.935, 0.96]

        labelLines(plt.gca().get_lines(), xvals=xvals, fontsize=15)

        x = np.arange(0, 1.1, 0.1)

        plt.plot(x, x * 0.3, linestyle="--", color="k", linewidth=1.8)
        plt.text(1.01, 0.295, "0.3", size=13)
        plt.plot(x, x * 0.5, linestyle="--", color="k", linewidth=1.8)
        plt.text(1.01, 0.495, "0.5", size=13)
        plt.plot(x, x * 0.8, linestyle="--", color="k", linewidth=1.8)
        plt.text(1.01, 0.795, "0.8", size=13)
        plt.plot(x, x, linestyle="--", color="k", linewidth=1.8)
        plt.text(1, 1, "1", size=13)
        plt.plot(x, x * 1.3, linestyle="--", color="k", linewidth=1.8)
        plt.text(0.76, 1.01, "1.3", size=13)
        plt.plot(x, x * 1.5, linestyle="--", color="k", linewidth=1.8)
        plt.text(0.65, 1.01, "1.5", size=13)
        plt.plot(x, x * 2, linestyle="--", color="k", linewidth=1.8)
        plt.text(0.5, 1.01, "2", size=13)
        plt.plot(x, x * 3, linestyle="--", color="k", linewidth=1.8)
        plt.text(0.327, 1.01, "3", size=13)
        plt.plot(x, x * 5, linestyle="--", color="k", linewidth=1.8)
        plt.text(0.2, 1.01, "5", size=13)
        plt.plot(x, x * 10, linestyle="--", color="k", linewidth=1.8)
        plt.text(0.09, 1.01, "10", size=13)

        plt.title("Performance Diagram " + self.model + " " + str(self.year), y=1.08)
        plt.scatter(np.mean(SR), np.mean(AR_POD), color="blue", s=200)
        plt.scatter(0.995, 0.995, color="orange", s=200, marker="D")
        plt.text(0.8, 0.96, "Perfect match", size=15)
        plt.xlabel("Success Ratio (1-FAR)", fontsize=20)
        plt.ylabel("Probability of detection (POD)", fontsize=20)
        plt.xlim(0, 1)
        plt.xticks((np.arange(0, 1.1, step=0.1)), fontsize=20)
        plt.yticks((np.arange(0, 1.1, step=0.1)), fontsize=20)
        plt.minorticks_on()
        plt.ylim(0, 1)

        plt.savefig(
            self.dir_plot
            + "PERFORMANCE_DIAG_"
            + self.model
            + "_"
            + str(self.year)
            + ".jpeg",
            bbox_inches="tight",
            dpi=600,
        )

        if self.show:
            plt.show()
