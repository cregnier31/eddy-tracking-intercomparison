import os
import fnmatch

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from labellines import labelLine, labelLines
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

data_crs = ccrs.PlateCarree()


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
        self.periods = (
            len(fnmatch.filter(os.listdir(general_info["PATH_DETECT_FILES"]), "*.*"))
            // 2
        )

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

        ax.plot(
            AC_x.T, AC_y.T, color="k", linestyle="-", linewidth=1, transform=data_crs
        )
        ax.plot(
            CC_x.T, CC_y.T, color="k", linestyle=":", linewidth=1.5, transform=data_crs
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
        else:
            pass

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
        NB_mean = np.full(len(t_data), np.mean(NB_EDDIES))

        fig, ax = plt.subplots(figsize=(12, 6))
        # ax = fig.add_axes([.03,.03,.94,.94])
        ax.plot(t_data, NB_EDDIES, color="black")
        ax.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.ylabel("Nb eddy detected")
        ax.plot(t_data, NB_mean, label="Mean", linestyle="--")
        ax.legend()

        plt.savefig(
            f"{self.dir_plot}NB_EDDIES_{self.model}_{self.year}.jpeg",
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
            f"{self.dir_plot}HIST2D_AMP_RAD_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

    def plot_histo_hits_false(self, radius_AR_hits, radius_AR_misses, radius_AR_falarm):
        bins = np.arange(0, 400, 3)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(
            radius_AR_hits,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="hits",
            color="green",
        )
        ax.hist(
            radius_AR_misses,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="misses",
            color="red",
        )
        ax.hist(
            radius_AR_falarm,
            bins=bins,
            fill=False,
            linewidth=3,
            histtype="step",
            label="false alarm",
            color="orange",
        )

        ax.set_ylim(0, 4500)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Radius (km)")
        ax.legend()
        ax.set_title(f"{self.model} Reference {self.reference}")
        plt.savefig(
            f"{self.dir_plot}HIST_MATCHING_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()

    def plot_pod_far_amplitude(self, POD_AR, FAR_AR):
        bins = np.arange(0, 400, 1)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        axes[0].step(bins[:-1], POD_AR, color="black", linewidth=2)
        axes[0].set(
            ylim=(np.nanmin(POD_AR) - 0.2, 1.05),
            ylabel="Probability of Detection",
            xlim=(0, 20),
            xlabel="Amplitude (cm)",
            xticks=np.arange(0, 20, 5),
        )
        axes[0].grid()

        axes[1].step(bins[:-1], FAR_AR, color="black", linewidth=2)
        axes[1].set(
            ylim=(0, np.nanmax(FAR_AR) + 0.2),
            ylabel="False Alarm Ratio",
            xlim=(0, 20),
            xlabel="Amplitude (cm)",
            xticks=np.arange(0, 20, 5),
        )
        axes[1].grid()

        fig.suptitle(f"{self.model} Reference {self.reference}")
        plt.tight_layout()
        plt.savefig(
            f"{self.dir_plot}POD_FAR_AMP_{self.model}_{self.year}.jpeg",
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
            f"{self.dir_plot}POD_FAR_TEMP_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
        )
        if self.show:
            plt.show()

    def perf_diag(self, SR, AR_POD):
        fig, ax = plt.subplots(figsize=(10, 10))

        CSI = np.arange(0.1, 1, 0.1)
        xvals = [0.57, 0.62, 0.77, 0.79, 0.85, 0.9, 0.95, 0.935, 0.96]
        labels = ["0.3", "0.5", "0.8", "1", "1.3", "1.5", "2", "3", "5", "10"]

        for c in CSI:
            i = np.arange(0, 1.1, 0.01)
            y = (c * i) / (c * i - c + i)
            indices = np.where(y <= 0.0)
            y = np.delete(y, indices)
            i = np.delete(i, indices)
            ax.plot(i, y, color="k", linewidth=1.8, label=str(np.round(c, 2)))

        labelLines(ax.get_lines(), xvals=xvals, fontsize=15)

        x = np.arange(0, 1.1, 0.1)
        y_offsets = [0.295, 0.495, 0.795, 1, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01]

        for i, label in enumerate(labels):
            ax.plot(x, x * float(label), linestyle="--", color="k", linewidth=1.8)
            ax.text(1.01, y_offsets[i], label, size=13)

        ax.set_title("Performance Diagram " + self.model + " " + str(self.year), y=1.08)
        ax.scatter(np.mean(SR), np.mean(AR_POD), color="blue", s=200)
        ax.scatter(0.995, 0.995, color="orange", s=200, marker="D")
        ax.text(0.8, 0.96, "Perfect match", size=15)
        ax.set_xlabel("Success Ratio (1-FAR)", fontsize=20)
        ax.set_ylabel("Probability of detection (POD)", fontsize=20)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks(np.arange(0, 1.1, step=0.1))
        ax.set_yticks(np.arange(0, 1.1, step=0.1))
        ax.tick_params(axis="both", which="both", labelsize=20)
        ax.minorticks_on()

        plt.savefig(
            f"{self.dir_plot}PERFORMANCE_DIAG_{self.model}_{self.year}.jpeg",
            bbox_inches="tight",
            dpi=600,
        )

        if self.show:
            plt.show()
