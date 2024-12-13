#!/usr/bin/python
# ****************************************************************#
# ScriptName: restore_from_downloads
# Author: @alibaba-inc.com
# Function:
# ***************************************************************#

import os
import sys

STRUCTURE_FILE_NAME = "structure.sql"
DATA_PATH_PREFIX = "data"


def create_database(db_host, db_port, db_user, db_pass, create_stmt_file):
    cmd = "mysql -h" + db_host + " -P" + db_port + " -u" + \
        db_user + " -p" + db_pass + " <" + create_stmt_file
    if os.system(cmd) != 0:
        print("[ERROR]: execute SQL failed. command: " + cmd)
        exit(1)


def create_table(db_host, db_port, db_user, db_pass, db_name, create_stmt_file):
    cmd = "mysql -h" + db_host + " -P" + db_port + " -u" + db_user + \
        " -p" + db_pass + " -D" + db_name + " <" + create_stmt_file
    if os.system(cmd) != 0:
        print("[ERROR]: execute SQL failed. command: " + cmd)
        exit(1)


def import_file_csv_with_header(db_host, db_port, db_user, db_pass, csv_file, db, table, with_header=False):
    if with_header:
        in_file = open(csv_file)
        schema = in_file.readline().strip('\n')
        load_cmd = "load data local infile \"" + csv_file + "\" into table `" + db + "`.`" + table + "` character set utf8mb4 FIELDS TERMINATED BY \",\" enclosed by \"\\\"\" lines terminated by \"\\n\" ignore 1 lines" + \
            " (" + schema + ")"
        in_file.close()
    else:
        load_cmd = "load data local infile \"" + csv_file + "\" into table `" + db + "`.`" + table + "` character set utf8mb4 FIELDS TERMINATED BY \",\" enclosed by \"\\\"\""
    
    cmd = "mysql --local_infile=1 -h" + db_host + " -P" + db_port + " -u" + \
        db_user + " -p" + db_pass + " -e '" + load_cmd + "'"

    print("[INFO]: trying to exec: " + cmd)
    if os.system(cmd) != 0:
        print("[ERROR]: execute SQL failed. command: " + cmd)
        exit(1)


def import_file_sql(db_host, db_port, db_user, db_pass, sql_file):
    cmd = "mysql -h" + db_host + " -P" + db_port + \
        " -u" + db_user + " -p" + db_pass + " <" + sql_file
    print("[INFO]: trying to exec: " + cmd)
    if os.system(cmd) != 0:
        print("[ERROR]: execute SQL failed. command: " + cmd)
        exit(1)


def print_usage():
    print(
        "Usage: python ./restore_mysql.py [backupset_directory] [database_host] [database_port] [database_username] [database_password]")


enable_foreign_key_check = None

def read_db_foreign_key_enable():
    global enable_foreign_key_check
    cmd = "mysql -h" + db_host + " -P" + db_port + " -u" + db_user + " -p" + db_pass + " -e " + "'SELECT @@FOREIGN_KEY_CHECKS'" # + " | awk '{print $1}' | sed -n '2,1p' "
    from subprocess import check_output
    try:
        cmd_output = check_output(cmd, shell=True)
        cmd_output = cmd_output.decode()
        foreign_check_enable = cmd_output.split("\n")[1]
        if foreign_check_enable == "1":
            print("[INFO]: foreign key check is on")
            enable_foreign_key_check = True
        elif foreign_check_enable == "0":
            print("[INFO]: foreign key check is off")
            enable_foreign_key_check = False
    except Exception:
        print("[WARN] try to get foreign key config failed. won't change foreign key config for MySQL")
        # do nothing


def do_disable_foreign_key_check():
    global enable_foreign_key_check
    if enable_foreign_key_check is True:
        print("[INFO]: try to disable foreign key check before importing data...")
        cmd = "mysql -h" + db_host + " -P" + db_port + " -u" + db_user + " -p" + db_pass + " -e " + "'SET GLOBAL FOREIGN_KEY_CHECKS=0'"
        if os.system(cmd) != 0:
            print("[ERROR]: execute SQL failed. command: " + cmd)
            exit(1)
        print("[INFO]: success disable foreign key check")
    else:
        print("[INFO]: no need to disable foreign key check before importing data")

def do_enable_foreign_key_check():
    global enable_foreign_key_check
    if enable_foreign_key_check is True:
        print("[INFO]: try to enable foreign key check after importing data...")
        cmd = "mysql -h" + db_host + " -P" + db_port + " -u" + db_user + " -p" + db_pass + " -e " + "'SET GLOBAL FOREIGN_KEY_CHECKS=1'"
        if os.system(cmd) != 0:
            print("[ERROR]: execute SQL failed. command: " + cmd)
            exit(1)
        print("[INFO]: success enable foreign key check")
    else:
        print("[INFO]: no need to enable foreign key check after importing data")

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print_usage()
        exit()

    root_dir = os.path.abspath(sys.argv[1])
    db_host = sys.argv[2]
    db_port = sys.argv[3]
    db_user = sys.argv[4]
    db_pass = sys.argv[5]
    print("[INFO]: restore data from " + root_dir +
          " to " + db_host + ":" + db_port)

    read_db_foreign_key_enable()

    do_disable_foreign_key_check()

    try:
        db_dirs = os.listdir(root_dir)
        for db_dir in db_dirs:
            dir_path = os.path.join(root_dir, db_dir)
            if not os.path.isdir(dir_path):
                continue
            db_structure_file = os.path.join(dir_path, STRUCTURE_FILE_NAME)
            create_database(db_host, db_port, db_user, db_pass, db_structure_file)
            print("[INFO]: restore structure database: " + db_dir + " ends")

            table_dirs = os.listdir(dir_path)
            for table_dir in table_dirs:
                table_dir_path = os.path.join(dir_path, table_dir)
                if not os.path.isdir(table_dir_path):
                    continue
                table_structure_file = os.path.join(table_dir_path, STRUCTURE_FILE_NAME)
                create_table(db_host, db_port, db_user, db_pass, db_dir, table_structure_file)
                print("[INFO]: restore structure table: " + table_dir + " ends")

                table_data_dir_path = os.path.join(table_dir_path, DATA_PATH_PREFIX)
                if not os.path.isdir(table_data_dir_path):
                    continue
                
                filename_slices = os.listdir(table_data_dir_path)[0].split(".")
                files_format = filename_slices[-1]
                if files_format == "csv":
                    with_header = len(filename_slices) > 1 and filename_slices[-2]=="wh" # .wh.csv is csv with header, .csv is csv without header
                    csv_files = os.listdir(table_data_dir_path)
                    csv_count = 0
                    for csv_file in csv_files:
                        csv_file_path = os.path.join(table_data_dir_path, csv_file)
                        file_size = os.path.getsize(csv_file_path)
                        if file_size > 0:
                            import_file_csv_with_header(db_host, db_port, db_user,
                                            db_pass, csv_file_path, db_dir, table_dir, with_header)
                            csv_count = csv_count + 1
                            print("[INFO]: restore data [" + str(csv_count) + "/" + str(
                                len(csv_files)) + "] of table " + db_dir + "." + table_dir)
                elif files_format == "sql":
                    sql_files = os.listdir(table_data_dir_path)
                    sql_count = 0
                    for sql_file in sql_files:
                        sql_file_path = os.path.join(table_data_dir_path, sql_file)
                        file_size = os.path.getsize(sql_file_path)
                        if file_size > 0:
                            import_file_sql(db_host, db_port,
                                            db_user, db_pass, sql_file_path)
                            sql_count = sql_count + 1
                            print("[INFO]: restore data [" + str(sql_count) + "/" + str(
                                len(sql_files)) + "] of table " + db_dir + "." + table_dir)
    finally:
        do_enable_foreign_key_check()
