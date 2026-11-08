import unittest
from datetime import datetime

from curb.engine import Detection, DwellEngine
from curb.models import Settings, Zone, validate_polygon


class EngineTests(unittest.TestCase):
    def engine(self, **kwargs):
        zone = Zone(id="curb",name="Lề đường",polygon=[[0,0],[.5,0],[.5,1],[0,1]],dwell_seconds=3,**kwargs)
        return DwellEngine([zone],Settings(still_window=1,minimum_area=0,movement_tolerance=.2,lost_grace=1))

    def det(self, tid=1,x=20):
        return Detection(tid,"car",(x-5,10,x+5,50))

    def test_stationary_alert_once(self):
        engine = self.engine()
        events = [e for t in range(10) for e in engine.update(t,[self.det()],100,100)]
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["alert_time_s"],3)

    def test_exit_zone_resets_timer(self):
        engine = self.engine()
        for t in range(3):
            engine.update(t,[self.det(x=48)],100,100)
        self.assertEqual(engine.update(3,[self.det(x=52)],100,100),[])
        self.assertEqual(len(engine.stops),0)

    def test_new_stop_same_position_not_suppressed(self):
        engine = self.engine()
        events = []
        for t in range(12):
            dets = [] if 4 <= t <= 6 else [self.det(tid=1 if t < 4 else 2)]
            events.extend(engine.update(t,dets,100,100))
        self.assertEqual(len(events),2)

    def test_returning_motion_is_not_stationary(self):
        engine = self.engine()
        events=[]
        for t in range(12):
            events.extend(engine.update(t,[self.det(x=15 if t%2 else 35)],100,100))
        self.assertEqual(events,[])

    def test_brief_id_change_preserves_episode(self):
        engine=self.engine()
        events=[]
        for t in range(8):
            events.extend(engine.update(t,[self.det(tid=1 if t<4 else 9)],100,100))
        self.assertEqual(len(events),1)

    def test_partial_occlusion_does_not_duplicate_alert(self):
        engine=self.engine()
        events=[]
        for step in range(45):
            t=step/5
            box=(15,10,25,35) if 4 <= t < 4.6 else (15,10,25,50)
            events.extend(engine.update(t,[Detection(1,"car",box)],100,100))
        self.assertEqual(len(events),1)

    def test_sustained_relocation_starts_new_stop(self):
        engine=self.engine()
        events=[]
        for step in range(60):
            t=step/5
            events.extend(engine.update(t,[self.det(x=20 if t<4 else 35)],100,100))
        self.assertEqual(len(events),2)
        self.assertGreaterEqual(events[1]["stop_start_s"],5)

    def test_unalerted_occlusion_does_not_shortcut_dwell(self):
        engine=self.engine()
        events=[]
        for step in range(35):
            t=step/5
            box=(15,10,25,35) if 2 <= t < 2.6 else (15,10,25,50)
            events.extend(engine.update(t,[Detection(1,"car",box)],100,100))
        self.assertTrue(events)
        self.assertGreaterEqual(events[0]["alert_time_s"],5.6)

    def test_overlapping_zones_independent(self):
        engine=self.engine()
        engine.zones.append(engine.zones[0].model_copy(update={"id":"other","name":"Vùng khác"}))
        events=[e for t in range(5) for e in engine.update(t,[self.det()],100,100)]
        self.assertEqual({e["zone_id"] for e in events},{"curb","other"})

    def test_class_filter_and_congestion(self):
        engine=self.engine(classes=["truck"])
        self.assertEqual([e for t in range(6) for e in engine.update(t,[self.det()],100,100)],[])
        engine=self.engine()
        self.assertEqual([e for t in range(6) for e in engine.update(t,[self.det(tid=i,x=10+i*10) for i in range(4)],100,100)],[])
        self.assertIn("curb",engine.congested)

    def test_invalid_polygons(self):
        for points in ([[0,0],[1,1],[0,1],[1,0]],[[0,0],[1,0],[1,0]],[[0,0],[2,0],[1,1]],[[0,0],[.5,.5],[1,1]]):
            with self.assertRaises(ValueError):
                validate_polygon(points)

    def test_video_clock_must_be_monotonic(self):
        engine=self.engine()
        engine.update(1,[],100,100)
        with self.assertRaises(ValueError):
            engine.update(0,[],100,100)

    def test_schedule_requires_recording_clock(self):
        engine=self.engine(schedule_enabled=True)
        with self.assertRaises(ValueError):
            engine.update(0,[self.det()],100,100)

    def test_schedule_overnight_belongs_to_start_day(self):
        engine=self.engine(schedule_enabled=True,start_time="22:00",end_time="06:00",weekdays=[0])
        monday=datetime(2026,11,9,23,0)
        tuesday=datetime(2026,11,10,2,0)
        self.assertEqual(len([e for t in range(5) for e in engine.update(t,[self.det()],100,100,monday)]),1)
        engine=self.engine(schedule_enabled=True,start_time="22:00",end_time="06:00",weekdays=[0])
        self.assertEqual(len([e for t in range(5) for e in engine.update(t,[self.det()],100,100,tuesday)]),1)
        engine=self.engine(schedule_enabled=True,start_time="22:00",end_time="06:00",weekdays=[0])
        self.assertEqual([e for t in range(5) for e in engine.update(t,[self.det()],100,100,datetime(2026,11,10,7))],[])

    def test_schedule_deactivation_resets_episode(self):
        engine=self.engine(schedule_enabled=True,start_time="08:00",end_time="09:00")
        for t in range(3):
            engine.update(t,[self.det()],100,100,datetime(2026,11,9,8,59))
        self.assertEqual(engine.update(3,[self.det()],100,100,datetime(2026,11,9,9,0)),[])
        self.assertEqual(len(engine.stops),0)


if __name__ == "__main__":
    unittest.main()
