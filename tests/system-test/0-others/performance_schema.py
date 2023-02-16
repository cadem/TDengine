###################################################################
#           Copyright (c) 2016 by TAOS Technologies, Inc.
#                     All rights reserved.
#
#  This file is proprietary and confidential to TAOS Technologies.
#  No part of this file may be reproduced, stored, transmitted,
#  disclosed or used in any form or by any means other than as
#  expressly provided by the written permission from Jianhui Tao
#
###################################################################

# -*- coding: utf-8 -*-


from util.log import *
from util.cases import *
from util.sql import *
from util.common import *
from util.sqlset import *
import threading
from taos.tmq import Consumer

class TDTestCase:
    def init(self, conn, logSql, replicaVar=1):
        self.replicaVar = int(replicaVar)
        tdLog.debug("start to execute %s" % __file__)
        tdSql.init(conn.cursor())
        self.conn=conn
        self.setsql = TDSetSql()
        self.dbname = 'db'
        self.stbname = 'stb'
        self.binary_length = 20 # the length of binary for column_dict
        self.nchar_length = 20  # the length of nchar for column_dict
        self.ts = 1537146000000
        self.user = "root"
        self.groupName = "tg2"
        self.topicName = "tmq_test_topic"
        self.appName = "python3.10" #todo need to set to fixed name
        self.ipAdd= "127.0.0.1";
        self.transTestDBName = "dbwithvgroup"
        self.column_dict = {
            'ts'  : 'timestamp',
            'col1': 'tinyint',
            'col2': 'smallint',
            'col3': 'int',
            'col4': 'bigint',
            'col5': 'tinyint unsigned',
            'col6': 'smallint unsigned',
            'col7': 'int unsigned',
            'col8': 'bigint unsigned',
            'col9': 'float',
            'col10': 'double',
            'col11': 'bool',
            'col12': f'binary({self.binary_length})',
            'col13': f'nchar({self.nchar_length})'
        }
        self.tbnum = 20
        self.rowNum = 10
        self.tag_dict = {
            't0':'int'
        }
        self.tag_values = [
            f'1'
            ]
        self.binary_str = 'taosdata'
        self.nchar_str = '涛思数据'
        self.ins_list = ['ins_dnodes','ins_mnodes','ins_modules','ins_qnodes','ins_snodes','ins_cluster','ins_databases','ins_functions',\
            'ins_indexes','ins_stables','ins_tables','ins_tags','ins_users','ins_grants','ins_vgroups','ins_configs','ins_dnode_variables',\
                'ins_topics','ins_subscriptions','ins_streams','ins_stream_tasks','ins_vnodes','ins_user_privileges']
        self.perf_list = ['perf_connections','perf_queries','perf_consumers','perf_trans','perf_apps']
    
    def insert_data(self,column_dict,tbname,row_num):
        insert_sql = self.setsql.set_insertsql(column_dict,tbname,self.binary_str,self.nchar_str)
        for i in range(row_num):
            insert_list = []
            self.setsql.insert_values(column_dict,i,insert_sql,insert_list,self.ts)

    def prepare_data(self):
        tdSql.execute(f"create database if not exists {self.dbname} vgroups 2")
        tdSql.execute(f'use {self.dbname}')

        tdSql.execute(self.setsql.set_create_stable_sql(self.stbname,self.column_dict,self.tag_dict))
        
        for i in range(self.tbnum):
            tdSql.execute(f"create table {self.stbname}_{i} using {self.stbname} tags({self.tag_values[0]})")
            self.insert_data(self.column_dict,f'{self.stbname}_{i}',self.rowNum)
        
        for i in range(self.tbnum):
            tdSql.execute(f"select * from {self.stbname}_{i}")

    class myThread (threading.Thread):
        def __init__(self, obj):
            threading.Thread.__init__(self)
            self.obj = obj
        def run(self):
            self.obj.transactionSQL()

    def transactionSQL(self):
        tdSqlTran = TDSql()
        tdSqlTran.init(self.conn.cursor())
        tdSqlTran.execute(f"create database if not exists %s vgroups 20"%(self.transTestDBName))
        tdSqlTran.execute(f"DROP DATABASE %s"%(self.transTestDBName))

    def init_tmq_env(self, db, topic):
        self.conn.execute("drop topic if exists {}".format(topic))
        self.conn.execute("create database if not exists {}".format(db))
        self.conn.select_db(db)
        self.conn.execute(
            "create stable if not exists stb_sub (ts timestamp, c1 int, c2 float, c3 varchar(16)) tags(t1 int, t3 varchar(16))")
        self.conn.execute("create topic if not exists {} as select ts, c1, c2, c3 from stb_sub".format(topic))

    def count_check(self):
        sleep(1) #performance table delay
        tdSql.query('select * from performance_schema.perf_apps')
        rowIndex = 0 #for debug
        tdSql.checkRows(1)
        tdSql.checkNotEqual(tdSql.queryResult[rowIndex][0], 0)          #column 0:app_id
        tdSql.checkEqual(tdSql.queryResult[rowIndex][1],self.ipAdd)     #column 1:ip
        tdSql.checkNotEqual(tdSql.queryResult[rowIndex][2], 0)          #column 2:pid
        tdLog.info(os.getppid())        #  not match               
        tdSql.checkEqual(tdSql.queryResult[rowIndex][3],self.appName)   #column 3:name              
        tdSql.checkNotEqual(tdSql.queryResult[rowIndex][4], 0)          #column 4:start_time
        tdSql.checkEqual(tdSql.queryResult[rowIndex][5], 0)             #column 5:insert_req       # zero ???
        tdSql.checkEqual(tdSql.queryResult[rowIndex][6],200)            #column 6:insert_row
        tdSql.checkNotEqual(tdSql.queryResult[rowIndex][7], 0)          #column 7:insert_time
        tdSql.checkEqual(tdSql.queryResult[rowIndex][8],32000)          #column 8:insert_bytes      #calculate this field
        tdSql.checkEqual(tdSql.queryResult[rowIndex][9], 0)             #column 9:fetch_bytes       # zero ???
        tdSql.checkNotEqual(tdSql.queryResult[rowIndex][10], 0)         #column 10:query_time       
        tdSql.checkEqual(tdSql.queryResult[rowIndex][11],0)             #column 11:slow_query       #how to construct a slow query
        tdSql.checkEqual(tdSql.queryResult[rowIndex][12],244)           #column 11:total_req
        tdSql.checkEqual(tdSql.queryResult[rowIndex][13], 1)            #column 13:current_req
        tdSql.checkNotEqual(tdSql.queryResult[rowIndex][14], 0)         #column 14:last_access


        tdSql.query('select * from performance_schema.perf_connections')
        tdSql.checkRows(2)
        for i in range(2):
            if tdSql.queryResult[i][2]== self.appName :
                tdSql.checkNotEqual(tdSql.queryResult[i][0],0)                  #column 0:conn_id
                tdSql.checkEqual(tdSql.queryResult[i][1],self.user)             #column 1:user
                tdSql.checkEqual(tdSql.queryResult[i][2],self.appName)          #column 2:app
                tdSql.checkNotEqual(tdSql.queryResult[i][3],0)                  #column 3:pid
                tdSql.checkNotEqual(tdSql.queryResult[i][4],0)                  #column 4:end_point
                tdSql.checkNotEqual(tdSql.queryResult[i][5],0)                  #column 5:login_time
                tdSql.checkNotEqual(tdSql.queryResult[i][6],0)                  #column 6:last_access
                self.connId = tdSql.queryResult[i][0]
            
        self.init_tmq_env(self.dbname, self.topicName)

        consumer = Consumer(
            {
                "group.id": self.groupName,
                "td.connect.user": self.user,
                "td.connect.pass": "taosdata",
                "td.connect.ip": self.ipAdd,
            }
        )
        consumer.subscribe([self.topicName])
        
        tdSql.query('select * from performance_schema.perf_consumers')
        tdSql.checkRows(1)
        tdSql.checkNotEqual(tdSql.queryResult[0][0],0)                  #consumer_id
        tdSql.checkEqual(tdSql.queryResult[0][1],self.groupName)        #consumer_group
        tdSql.checkNotEqual(tdSql.queryResult[0][2],0)                  #client_id
        tdSql.checkEqual(tdSql.queryResult[0][3],"ready")               #status
        tdSql.checkEqual(tdSql.queryResult[0][4],self.topicName)        #topics
        tdSql.checkNotEqual(tdSql.queryResult[0][5],0)                  #up_time
        tdSql.checkNotEqual(tdSql.queryResult[0][6],0)                  #subscribe_time
        tdSql.checkNotEqual(tdSql.queryResult[0][7],0)                  #rebalance_time

        sleep(3) #performance_schema delay, wait for last query

        tdSql.query('select * from performance_schema.perf_queries')
        tdSql.checkEqual(tdSql.queryResult[0][12],"select * from performance_schema.perf_consumers") #sql
        tdSql.checkNotEqual(tdSql.queryResult[0][0],0)                  #kill_id
        tdSql.checkNotEqual(tdSql.queryResult[0][1],0)                  #query_id
        tdSql.checkEqual(tdSql.queryResult[0][2],self.connId)           #conn_id
        tdSql.checkEqual(tdSql.queryResult[0][3],self.appName)          #app
        tdSql.checkNotEqual(tdSql.queryResult[0][4],0)                  #pid
        tdSql.checkEqual(tdSql.queryResult[0][5],self.user)             #user
        tdSql.checkNotEqual(tdSql.queryResult[0][6],0)                  #end_point
        tdSql.checkNotEqual(tdSql.queryResult[0][7],0)                  #create_time
        tdSql.checkNotEqual(tdSql.queryResult[0][8],0)                  #exec_usec
        tdSql.checkEqual(tdSql.queryResult[0][9],0)                     #stable_query
        tdSql.checkEqual(tdSql.queryResult[0][10],1)                    #sub_num
        tdSql.checkEqual(tdSql.queryResult[0][11],"243:SUCCEED")        #sub_status   

        t1 = self.myThread(self) 
        t1.start()                           
        
        sleep(0.5) # there is delay
        tdSql.query('select * from performance_schema.perf_trans')
        tdSql.checkNotEqual(tdSql.queryResult[0][0],0)                  #id
        tdSql.checkNotEqual(tdSql.queryResult[0][1],0)                  #create_time
        tdSql.checkEqual(tdSql.queryResult[0][2],"redoAction")          #stage
        tdSql.checkEqual(tdSql.queryResult[0][3],"create-db")           #oper
        tdSql.checkEqual(tdSql.queryResult[0][4],self.transTestDBName)  #db
        tdSql.checkNotEqual(tdSql.queryResult[0][5],0)                  #stable
        tdSql.checkEqual(tdSql.queryResult[0][6],0)                     #failed_times
        tdSql.checkNotEqual(tdSql.queryResult[0][7],0)                  #last_exec_time
        tdSql.checkNotEqual(tdSql.queryResult[0][8],0)                  #last_action_info

        t1.join()

        #tdSql.query('select count(*) from performance_schema.perf_smas')
        #tdSql.checkEqual(tdSql.queryResult[0][0],0)
    def run(self):
        self.prepare_data()
        self.count_check()

    def stop(self):
        tdSql.close()
        tdLog.success("%s successfully executed" % __file__)

tdCases.addWindows(__file__, TDTestCase())
tdCases.addLinux(__file__, TDTestCase())