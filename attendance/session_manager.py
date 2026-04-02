import sqlite3
from datetime import datetime, time, timedelta
from config import Config
from database.database import DB_NAME, init_session, update_session_attendance, clear_session_logs

class SessionManager:
    """
    Manages end-of-session attendance calculation.
    """
    def __init__(self):
        # Use threshold from global config
        self.attendance_threshold = timedelta(minutes=Config.ATTENDANCE_THRESHOLD_MINUTES)
        
        # Define period boundaries
        self.morning_periods = {
            'P1': (time(8, 30), time(9, 25)),
            'P2': (time(9, 25), time(10, 20)),
            'P3': (time(10, 35), time(11, 30)),
            'P4': (time(11, 30), time(12, 25))
        }
        
        self.afternoon_periods = {
            'P5': (time(13, 15), time(14, 10)),
            'P6': (time(14, 10), time(15, 5)),
            'P7': (time(15, 5), time(16, 0))
        }

    def _get_overlap(self, interval_start, interval_end, period_start, period_end):
        """
        Calculates overlap duration between two time intervals.
        """
        start = max(interval_start, period_start)
        end = min(interval_end, period_end)
        
        if start < end:
            return end - start
        return timedelta(0)

    def _process_student_intervals(self, events, period_def, target_date):
        """
        Calculates attendance for a single student against defined periods.
        """
        intervals = []
        bus_delayed = False
        i = 0
        while i < len(events):
            if events[i]['bus_delay_flag']:
                bus_delayed = True
                
            if events[i]['event_type'] == 'ENTRY':
                entry_time = events[i]['dt']
                exit_time = None
                
                # Look ahead for next EXIT
                if i + 1 < len(events) and events[i+1]['event_type'] == 'EXIT':
                    exit_time = events[i+1]['dt']
                    i += 2
                else:
                    # Missing exit, handled by _ensure_automatic_exits
                    i += 1
                    continue
                
                intervals.append((entry_time, exit_time))
            else:
                # Orphaned exit, skip
                i += 1

        results = {}
        for p_name, (p_start_time, p_end_time) in period_def.items():
            p_start = datetime.combine(target_date, p_start_time)
            p_end = datetime.combine(target_date, p_end_time)
            
            total_overlap = timedelta(0)
            for (int_start, int_end) in intervals:
                overlap = self._get_overlap(int_start, int_end, p_start, p_end)
                total_overlap += overlap
            
            # Bus delay override for P1
            if p_name == 'P1' and bus_delayed:
                results[p_name] = 'P'
            elif total_overlap >= self.attendance_threshold:
                results[p_name] = 'P'
            else:
                results[p_name] = 'A'
                
        return results

    def _ensure_automatic_exits(self, session_type, target_date):
        """
        Automatically inserts an EXIT event if the last event was an ENTRY.
        """
        now = datetime.now()
        
        if session_type == 'Morning':
            session_end_time = time(12, 25)
        else:
            session_end_time = time(16, 0)
            
        session_end_dt = datetime.combine(target_date, session_end_time)
        
        # Safety Check: Do not append if time hasn't passed (unless in debug)
        if now < session_end_dt and not Config.DEBUG:
            print(f"Cannot run end-of-session calculations for {session_type} yet.")
            return False

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Get latest event per student for today's session
        cursor.execute('''
            SELECT student_id, event_type, MAX(id)
            FROM policy_logs
            WHERE date = ? AND session_type = ?
            GROUP BY student_id
        ''', (target_date.strftime('%Y-%m-%d'), session_type))
        
        last_events = cursor.fetchall()
        
        for student_id, event_type, last_id in last_events:
            if event_type == 'ENTRY':
                # Insert a dummy EXIT event at exactly the session end time
                cursor.execute('''
                    INSERT INTO policy_logs (
                        student_id, timestamp, date, 
                        event_type, period, session_type, 
                        late_entry, bus_delay
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student_id, 
                    session_end_dt.strftime('%Y-%m-%d %H:%M:%S'), 
                    target_date.strftime('%Y-%m-%d'), 
                    'EXIT', 
                    'P4' if session_type == 'Morning' else 'P7',
                    session_type, 
                    0, 0
                ))
                
        conn.commit()
        conn.close()
        return True

    def _fetch_session_events(self, session_type, target_date):
        """
        Returns a dict mapping student_id -> list of event dicts
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, timestamp, event_type, bus_delay
            FROM policy_logs
            WHERE date = ? AND session_type = ?
            ORDER BY student_id, timestamp ASC
        ''', (target_date.strftime('%Y-%m-%d'), session_type))
        
        rows = cursor.fetchall()
        conn.close()
        
        events_by_student = {}
        for student_id, ts_str, event_type, bus_delay_flag in rows:
            if student_id not in events_by_student:
                events_by_student[student_id] = []
                
            events_by_student[student_id].append({
                'dt': datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S'),
                'event_type': event_type,
                'bus_delay_flag': bool(bus_delay_flag)
            })
            
        return events_by_student

    def finalize_session(self, session_type, progress_callback=None):
        """
        Main entry point to calculate attendance and clear logs.
        """
        now = datetime.now()
        target_date = now.date()
        
        if progress_callback: progress_callback(f"Finalizing {session_type} session...")
        
        # Step 1: Safety check & Auto exits
        if not self._ensure_automatic_exits(session_type, target_date):
            return False
            
        # Step 2: Initialize Session Table
        init_session(session_type)
        
        # Step 3: Calculation Overlaps
        events_by_student = self._fetch_session_events(session_type, target_date)
        period_def = self.morning_periods if session_type == 'Morning' else self.afternoon_periods
        
        for student_id, events in events_by_student.items():
            results = self._process_student_intervals(events, period_def, target_date)
            
            # Update DB (the actual table - morning_attendance or afternoon_attendance - is handled in database.py)
            for period, status in results.items():
                if status == 'P':
                    update_session_attendance(student_id, period, status, session_type)
                    
        # Step 4: Cleanup
        clear_session_logs(session_type, target_date.strftime('%Y-%m-%d'))
        
        if progress_callback: progress_callback("Session finalized successfully.")
        return True

