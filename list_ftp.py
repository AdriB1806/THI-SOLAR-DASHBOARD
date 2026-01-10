#!/usr/bin/env python3
import ftplib

HOST = 'jupyterhub-wi'
USER = 'ftpuser'
PASS = 'ftpuser123'

def try_list(ftp, path):
    print(f"\n-- Listing: {path}")
    try:
        lines = []
        ftp.retrlines(f'LIST {path}', lines.append)
        for l in lines:
            print(l)
    except Exception:
        try:
            names = ftp.nlst(path)
            for n in names:
                try:
                    s = ftp.size(n)
                    print(f'FILE {n} size={s}')
                except Exception:
                    print('ENTRY', n)
        except Exception as e:
            print('Could not list', path, e)

def walk(ftp, path):
    try:
        names = ftp.nlst(path)
    except Exception:
        return
    for n in names:
        if n in ('.', '..'):
            continue
        full = n if path in ('.', '') else f"{path}/{n}"
        # detect directory by trying to cwd
        try:
            ftp.cwd(full)
            print('\nDIR:', full)
            walk(ftp, full)
            ftp.cwd('..')
        except Exception:
            try:
                s = ftp.size(full)
                print(f'FILE: {full} size={s}')
            except Exception:
                print('UNKNOWN:', full)

def main():
    try:
        ftp = ftplib.FTP(HOST, timeout=10)
        ftp.login(USER, PASS)
        print('Connected to FTP:', HOST)

        # top-level
        try:
            top = ftp.nlst()
            print('\nTop-level entries:')
            for t in top:
                print('-', t)
        except Exception as e:
            print('Top-level nlst failed:', e)

        # list pvdaten if exists
        try_list(ftp, 'pvdaten')

        # recursive walk of pvdaten
        print('\nRecursive walk of pvdaten:')
        walk(ftp, 'pvdaten')

        ftp.quit()
    except Exception as e:
        print('FTP connection error:', e)

if __name__ == '__main__':
    main()
