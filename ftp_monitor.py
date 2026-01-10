#!/usr/bin/env python3
"""Simple FTP monitor: polls MDTM and downloads when file changes.

Usage: python3 ftp_monitor.py --iterations 10 --interval 30
"""
import ftplib
import time
import os
import argparse
import datetime

HOST = 'jupyterhub-wi'
USER = 'ftpuser'
PASS = 'ftpuser123'
PATH = 'pvdaten/pv.csv'
LOCAL = 'pv.csv'
SNAP_DIR = 'pv_csv_snapshots'
LOG_FILE = 'ftp_monitor.log'


def log(msg):
    ts = datetime.datetime.utcnow().isoformat() + 'Z'
    line = f"{ts} {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def get_mdtm():
    try:
        ftp = ftplib.FTP(HOST, timeout=10)
        ftp.login(USER, PASS)
        resp = ftp.sendcmd('MDTM ' + PATH)
        ftp.quit()
        if resp.startswith('213 '):
            return resp.split()[1]
    except Exception as e:
        log(f"MDTM error: {e}")
    return None


def download_to(path):
    try:
        ftp = ftplib.FTP(HOST, timeout=10)
        try:
            ftp.login(USER, PASS)
            remote_dir, remote_name = os.path.split(PATH)
            if remote_dir:
                ftp.cwd(remote_dir)
            with open(path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_name}', f.write)
        finally:
            try:
                ftp.quit()
            except Exception:
                pass
        return True
    except Exception as e:
        log(f"Download error: {e}")
        return False


def ensure_dir(d):
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def main(iterations, interval):
    """Run the monitor.

    If `iterations` <= 0, run continuously until killed (sleeping `interval` seconds between checks).
    Otherwise run the given number of iterations.
    """
    ensure_dir(SNAP_DIR)
    prev_mdtm = None

    def _one_check(iteration_label):
        nonlocal prev_mdtm
        log(f"{iteration_label}: checking MDTM")
        mdtm = get_mdtm()
        if mdtm is None:
            log("Could not get MDTM (server may not support it or connection failed)")
            return

        log(f"MDTM: {mdtm}")
        if prev_mdtm is None:
            log("Initial fetch: downloading file")
            if download_to(LOCAL):
                snap_name = os.path.join(SNAP_DIR, f"pv_{mdtm}.csv")
                download_to(snap_name)
                log(f"Saved initial snapshot: {snap_name}")
            else:
                log("Initial download failed")
        elif mdtm != prev_mdtm:
            log(f"Change detected (prev={prev_mdtm}) -> downloading new snapshot")
            snap_name = os.path.join(SNAP_DIR, f"pv_{mdtm}.csv")
            if download_to(snap_name):
                download_to(LOCAL)
                log(f"Saved snapshot: {snap_name}")
            else:
                log("Snapshot download failed")
        else:
            log("No change detected")

        prev_mdtm = mdtm

    if iterations <= 0:
        count = 0
        while True:
            count += 1
            try:
                _one_check(f"Iteration {count} (continuous)")
            except Exception as e:
                log(f"Check error: {e}")
            time.sleep(interval)
    else:
        for i in range(iterations):
            try:
                _one_check(f"Iteration {i+1}/{iterations}")
            except Exception as e:
                log(f"Check error: {e}")
            if i < iterations - 1:
                time.sleep(interval)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='FTP monitor for pv.csv')
    p.add_argument('--iterations', type=int, default=6, help='Number of polling iterations')
    p.add_argument('--interval', type=int, default=10, help='Seconds between iterations')
    args = p.parse_args()
    main(args.iterations, args.interval)
