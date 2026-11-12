import json
import unittest
from pathlib import Path
from engine.process import Process,simulate
from engine.memory import simulate_memory
from engine.filesystem import FileSystem
from engine.parallel import simulate_parallel
from engine.synchronization import demonstrate,race_demo,detect_deadlock
from engine.baselines import run_baselines

ROOT=Path(__file__).resolve().parents[1]
BASE=[Process('P1',0,8,2),Process('P2',1,4,1),Process('P3',2,2,3),Process('P4',4,5,2)]

class SchedulingTests(unittest.TestCase):
    def test_fcfs_exact(self):
        r=simulate([Process('A',0,3),Process('B',1,2)])
        self.assertEqual([(s['pid'],s['start'],s['end']) for s in r['gantt']],[('A',0,3),('B',3,5)])
        self.assertEqual([p['waiting'] for p in r['processes']],[0,2])
        self.assertEqual(r['metrics']['context_switches'],1)
    def test_sjf(self):
        r=simulate([Process('A',0,5),Process('B',0,2),Process('C',0,1)],'SJF')
        self.assertEqual([s['pid'] for s in r['gantt']],['C','B','A'])
    def test_srtf(self):
        r=simulate([Process('A',0,6),Process('B',1,2)],'SRTF')
        self.assertEqual([s['pid'] for s in r['gantt']],['A','B','A'])
    def test_rr(self):
        r=simulate([Process('A',0,5),Process('B',0,2)],'Round Robin',quantum=2)
        self.assertEqual([s['pid'] for s in r['gantt']],['A','B','A'])
    def test_priority_aging(self):
        r=simulate([Process('A',0,10,1),Process('B',0,2,4)],'Priority with Aging',aging_interval=1)
        self.assertEqual(r['processes'][1]['completion'] < 12,True)
    def test_io_states(self):
        r=simulate([Process('A',0,4,io_start=2,io_duration=3)])
        self.assertIn('Blocked',[e['state'] for e in r['events']])
        self.assertEqual(r['processes'][0]['completion'],7)
        self.assertEqual(r['processes'][0]['waiting'],0)
    def test_replay(self):
        self.assertEqual(simulate(BASE,'SRTF'),simulate(BASE,'SRTF'))
    def test_invalid(self):
        for workload in ([],[Process('A',0,0)],[Process('A',0,1),Process('A',1,2)],[Process('A',-1,1)]):
            with self.assertRaises(ValueError):simulate(workload)
    def test_boundary(self):
        r=simulate([Process('A',0,1)])
        self.assertEqual(r['metrics']['cpu_utilization'],100)
        self.assertEqual(r['metrics']['context_switches'],0)
    def test_context_cost(self):
        r=simulate([Process('A',0,2),Process('B',0,1)],context_cost=2)
        self.assertEqual(r['metrics']['makespan'],5)
        self.assertEqual(r['metrics']['context_switches'],1)
    def test_tie_break(self):
        r=simulate([Process('Z',0,1),Process('A',0,1)])
        self.assertEqual([s['pid'] for s in r['gantt']],['Z','A'])

class OtherTests(unittest.TestCase):
    def test_memory(self):
        r=simulate_memory([0,4096,0,8192],4096,2)
        self.assertEqual((r['hits'],r['faults'],r['evictions']),(1,3,1))
    def test_file(self):
        fs=FileSystem();fs.execute('mkdir','/a');fs.execute('mkfile','/a/f');fs.execute('write','/a/f','hi')
        self.assertEqual(fs.execute('cat','/a/f'),'hi')
        with self.assertRaises(ValueError):fs.execute('rmdir','/a')
    def test_parallel(self):
        tasks=[{'pid':f'P{i}','arrival':0,'burst':4} for i in range(4)]
        self.assertEqual(simulate_parallel(tasks,1)['parallel_time'],16)
        self.assertEqual(simulate_parallel(tasks,4)['parallel_time'],4)
    def test_sync(self):
        for method in ('Mutex / Lock','Semaphore','Barrier'):self.assertTrue(demonstrate(method,4,50)['pass'])
        self.assertGreater(race_demo()['lost'],0)
    def test_deadlock(self):
        self.assertTrue(detect_deadlock([('A','B'),('B','A')]))
        self.assertFalse(detect_deadlock([('A','B'),('B','C')]))
    def test_baselines(self):
        self.assertTrue(all(r['status']=='PASS' for r in run_baselines(ROOT/'data')))

if __name__=='__main__':unittest.main()
