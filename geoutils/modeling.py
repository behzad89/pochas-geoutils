# Name: modeling.py
# Description: The tools to prepare the model pipeline with additional functions for visualization
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date:28.02.2022


# Packages
from typing import List
import pandas as pd
import numpy as np
import numpy.typing as npt

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import (
    train_test_split,
    cross_validate,
    GridSearchCV,
    KFold,
    TimeSeriesSplit,
    GroupKFold,
)
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import geopandas as gpd

import matplotlib.pyplot as plt
import seaborn as sns

from typing import List
import os, sys


def cal_error_metrics(y: npt.ArrayLike, y_pred: npt.ArrayLike):
    """
    Calculation of the error metrics
    
    :param y: True values for dependant variable
    :param y_pred: Predicted values for dependant variable 
    :return: return the the RMSE,MSE,MAE,R2

    """
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    train_test_full_error = pd.DataFrame(
        {"RMSE": [rmse], "MSE": [mse], "MAE": [mae], "R2": r2}
    )
    return train_test_full_error


def scatter_plot(y: npt.ArrayLike, y_pred: npt.ArrayLike):
    """
    scatter plot the true vaues and predicted values

    :param y: True values for dependant variable
    :param y_pred: Predicted values for dependant variable 
    :return: The scatter plot
    """
    plt.figure(figsize=(8, 8))
    plt.scatter(y, y_pred)
    plt.xlabel("True values")
    plt.ylabel("Predicted values")
    plt.show()


def plot_trend(y: npt.ArrayLike, y_pred: npt.ArrayLike, xlim: tuple = None):

    """
    Plot the trend of predicted and true dependant variable

    :param y: True values for dependant variable
    :param y_pred: Predicted values for dependant variable
    :param y_pred: Determine the specific time-extend to focus on
    :return: The trend plot
    """
    plt.figure(figsize=(16, 8))
    plt.plot(y, color="k", alpha=0.3, lw=1, label="True values")
    plt.plot(y_pred, color="b", lw=1, label="Predicted values")
    plt.legend()
    plt.xlabel("Time")

    if xlim != None:
        plt.xlim(xlim)
    plt.show()


def temperal_cross_validation(
    model, X: pd.DataFrame, y: pd.Series, num_split: int = 5, csv_path: str = None
):

    """
    Implement temporal cross-validation and calculate the error metrics

    :param model: Trained model
    :param X: predictors
    :param y: dependant variable
    :param num_split: Number of folds
    :param csv_path: The path the CSV should be saved
    :return: calculated the error metrics for each fold with average of them
    """
    num_split = num_split
    cv = KFold(num_split)
    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=[
            "neg_root_mean_squared_error",
            "neg_mean_squared_error",
            "neg_mean_absolute_error",
            "r2",
        ],
        return_train_score=True,
        n_jobs=-1,
    )

    df_err = pd.DataFrame(scores).T[2:]
    df_err[:6] = df_err[:6] * -1
    df_err.index = index = [
        "test_root_mean_squared_error",
        "train_root_mean_squared_error",
        "test_mean_squared_error",
        "train_mean_squared_error",
        "test_mean_absolute_error",
        "train_mean_absolute_error",
        "test_r2",
        "train_r2",
    ]
    df_err.columns = [f"Fold 0{i}" for i in np.arange(1, num_split + 1)]
    df_err.loc[:, "Average_Error"] = df_err.mean(axis=1)

    if csv_path != None:
        df_err.to_csv(csv_path)

    return df_err


def plot_temporal_folds(X: pd.DataFrame, num_split: int = 5):
    """
    Plot the temporal cross-validation

    :param X: predictors
    :param num_split: Number of folds
    :return: folds of temperal cross-validation

    """

    fig, ax = plt.subplots(figsize=(10, 5))
    cv = KFold(num_split)
    for ii, (tr, tt) in enumerate(cv.split(X)):
        ax.scatter(tr, [ii] * len(tr), marker="_", s=10, linewidths=40, c="blue")
        ax.scatter(tt, [ii] * len(tt), marker="_", s=10, linewidths=40, c="red")
    plt.show()


def spatial_cross_validation(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    stations: pd.Series,
    num_split=5,
    csv_path=None,
):
    """
    Implement spatial cross-validation and calculate the error metrics

    :param model: Trained model
    :param X: predictors
    :param y: dependant variable
     :param stations: The column which includes the name of the stations
    :param num_split: Number of folds
    :param csv_path: The path the CSV should be saved
    :return: calculated the error metrics for each fold with average of them
  
    """
    stns = stations.values
    group_kfold = GroupKFold(n_splits=num_split)
    cv = group_kfold.split(X, groups=stns)
    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=[
            "neg_root_mean_squared_error",
            "neg_mean_squared_error",
            "neg_mean_absolute_error",
            "r2",
        ],
        return_train_score=True,
        n_jobs=-1,
    )

    df_err = pd.DataFrame(scores).T[2:]
    df_err[:6] = df_err[:6] * -1
    df_err.index = index = [
        "test_root_mean_squared_error",
        "train_root_mean_squared_error",
        "test_mean_squared_error",
        "train_mean_squared_error",
        "test_mean_absolute_error",
        "train_mean_absolute_error",
        "test_r2",
        "train_r2",
    ]

    df_err.columns = [f"Fold 0{i}" for i in np.arange(1, num_split + 1)]
    df_err.loc[:, "Average_Error"] = df_err.mean(axis=1)

    if csv_path != None:
        df_err.to_csv(csv_path)

    return df_err


def plot_spatial_cross_validatoion(
    data: pd.DataFrame,
    station_column: str,
    n_splits: int,
    map: str = None,
    title: bool = False,
):
    """
    Plot the Spatial cross-validation

    :param data: Source data include dependant and independent variables
    :param station_column: Column which includes the name of the stations
    :param num_split: Number of folds
    :param map: Path to vector shp or geojson file to plot
    :param title: Should the tile should be plot for the figure or not
    :return: folds of spatial cross-validation

    """

    fig, ax = plt.subplots(
        1, n_splits, figsize=(n_splits * 8, 5), constrained_layout=True
    )

    if map != None:
        ch = gpd.read_file(map)

    stns = data[station_column].values
    group_kfold = GroupKFold(n_splits=n_splits)
    cv = group_kfold.split(data, groups=stns)

    for i, (tr, tt) in enumerate(cv):
        x_tr = data.x.iloc[tr].unique()
        y_tr = data.y.iloc[tr].unique()

        x_tt = data.x.iloc[tt].unique()
        y_tt = data.y.iloc[tt].unique()

        tr_coord = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x_tr, y_tr))
        tt_coord = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x_tt, y_tt))

        tr_coord.plot(ax=ax[i - 1], color="Blue", markersize=20, label="Train")
        tt_coord.plot(ax=ax[i - 1], color="Red", markersize=20, label="Test")
        if map != None:
            ch.plot(
                ax=ax[i - 1], alpha=1, facecolor="none", edgecolor="black", linewidth=1
            )
        ax[i - 1].legend()
    if title == True:
        fig.suptitle(f"Spatial cross-validation with {n_splits} folds")
    plt.show()

