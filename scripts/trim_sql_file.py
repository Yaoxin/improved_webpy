__author__ = 'Pure'

import sys


def trim_sql_file(file_name):
    '''
    trim sql file to a simple format.
    :return:
    '''
    line_list = list()
    with open(file_name, 'r') as f:
        for line in f:
            if not line.startswith("/*"):
                if line.find("AUTO_INCREMENT=") != -1:
                    line = ") ENGINE=InnoDB DEFAULT CHARSET=utf8 " + line[line.rfind('COMMENT'):]
                line_list.append(line)

    out_file = "trim_%s" % file_name
    with open(out_file, 'w+') as f:
        f.writelines(line_list)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "python trim_sql_file.py [file_name]"
    else:
        trim_sql_file(sys.argv[1])



