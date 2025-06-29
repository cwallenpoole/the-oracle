#!/usr/bin/env python3
"""
Performance monitoring script for The Oracle I Ching App

This script provides real-time performance monitoring and profiling capabilities:
- Memory usage tracking
- Database query performance
- Response time monitoring
- Bottleneck identification
- Resource usage alerts
"""

import time
import psutil
import sqlite3
import threading
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class PerformanceMonitor:
    """Real-time performance monitoring for the I Ching app"""

    def __init__(self, db_file="data/users.db"):
        self.db_file = db_file
        self.start_time = time.time()
        self.metrics = {
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100),
            'db_query_times': deque(maxlen=100),
            'response_times': deque(maxlen=100),
            'error_count': 0,
            'request_count': 0
        }
        self.alerts = []
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, interval=5):
        """Start continuous monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"Performance monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Performance monitoring stopped")

    def _monitor_loop(self, interval):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent(interval=1)

                self.metrics['memory_usage'].append({
                    'timestamp': time.time(),
                    'value': memory_percent
                })

                self.metrics['cpu_usage'].append({
                    'timestamp': time.time(),
                    'value': cpu_percent
                })

                # Check for alerts
                self._check_alerts(memory_percent, cpu_percent)

                # Test database performance
                self._test_database_performance()

                time.sleep(interval)

            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(interval)

    def _check_alerts(self, memory_percent, cpu_percent):
        """Check for performance alerts"""
        current_time = datetime.now()

        # Memory usage alert
        if memory_percent > 80:
            alert = {
                'type': 'HIGH_MEMORY',
                'value': memory_percent,
                'timestamp': current_time,
                'message': f"High memory usage: {memory_percent:.1f}%"
            }
            self.alerts.append(alert)
            print(f"⚠️  ALERT: {alert['message']}")

        # CPU usage alert
        if cpu_percent > 80:
            alert = {
                'type': 'HIGH_CPU',
                'value': cpu_percent,
                'timestamp': current_time,
                'message': f"High CPU usage: {cpu_percent:.1f}%"
            }
            self.alerts.append(alert)
            print(f"⚠️  ALERT: {alert['message']}")

    def _test_database_performance(self):
        """Test database query performance"""
        try:
            start_time = time.time()

            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()

            # Test query
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM history")
            history_count = c.fetchone()[0]

            conn.close()

            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            self.metrics['db_query_times'].append({
                'timestamp': time.time(),
                'value': query_time,
                'user_count': user_count,
                'history_count': history_count
            })

            # Alert for slow queries
            if query_time > 100:  # > 100ms
                alert = {
                    'type': 'SLOW_QUERY',
                    'value': query_time,
                    'timestamp': datetime.now(),
                    'message': f"Slow database query: {query_time:.1f}ms"
                }
                self.alerts.append(alert)
                print(f"⚠️  ALERT: {alert['message']}")

        except Exception as e:
            print(f"Database performance test failed: {e}")

    def profile_user_operations(self, num_operations=100):
        """Profile user-related operations"""
        print(f"\nProfiling {num_operations} user operations...")

        from models.user import User
        import tempfile

        # Create temporary database
        test_db_fd, test_db_path = tempfile.mkstemp()

        try:
            # Profile user creation
            start_time = time.time()
            for i in range(num_operations):
                user = User(f"perftest{i}", "hash123", "1990-01-01", f"Profile test {i}")
                user.db_file = test_db_path
                user.save()

            creation_time = time.time() - start_time

            # Profile user retrieval
            start_time = time.time()
            for i in range(num_operations):
                user = User.get_by_username(f"perftest{i}")

            retrieval_time = time.time() - start_time

            # Profile user authentication
            start_time = time.time()
            for i in range(num_operations):
                User.authenticate(f"perftest{i}", "hash123")

            auth_time = time.time() - start_time

            print(f"User creation: {creation_time:.3f}s ({creation_time/num_operations*1000:.1f}ms per operation)")
            print(f"User retrieval: {retrieval_time:.3f}s ({retrieval_time/num_operations*1000:.1f}ms per operation)")
            print(f"User authentication: {auth_time:.3f}s ({auth_time/num_operations*1000:.1f}ms per operation)")

            # Cleanup
            os.close(test_db_fd)
            os.unlink(test_db_path)

        except Exception as e:
            print(f"User profiling failed: {e}")
            os.close(test_db_fd)
            os.unlink(test_db_path)

    def profile_iching_operations(self, num_operations=100):
        """Profile I Ching operations"""
        print(f"\nProfiling {num_operations} I Ching operations...")

        try:
            from logic.iching import cast_hexagrams, get_hexagram_section

            # Profile hexagram casting
            start_time = time.time()
            for _ in range(num_operations):
                reading = cast_hexagrams()

            casting_time = time.time() - start_time

            # Profile text retrieval
            start_time = time.time()
            for i in range(1, min(num_operations + 1, 65)):  # Max 64 hexagrams
                hexagram = get_hexagram_section(i)

            text_time = time.time() - start_time

            print(f"Hexagram casting: {casting_time:.3f}s ({casting_time/num_operations*1000:.1f}ms per operation)")
            print(f"Text retrieval: {text_time:.3f}s ({text_time/min(num_operations, 64)*1000:.1f}ms per operation)")

        except Exception as e:
            print(f"I Ching profiling failed: {e}")

    def analyze_database_size(self):
        """Analyze database size and growth"""
        print("\nDatabase Analysis:")

        try:
            # Get database file size
            db_size = os.path.getsize(self.db_file) / 1024  # KB
            print(f"Database size: {db_size:.1f} KB")

            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()

            # Count records
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM history")
            history_count = c.fetchone()[0]

            # Get table sizes (approximate)
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()

            print(f"Users: {user_count}")
            print(f"History entries: {history_count}")

            if user_count > 0:
                print(f"Average database size per user: {db_size/user_count:.1f} KB")

            if history_count > 0:
                print(f"Average history entries per user: {history_count/max(user_count, 1):.1f}")

            # Check for large history entries
            c.execute("SELECT LENGTH(reading) as reading_length FROM history ORDER BY reading_length DESC LIMIT 5")
            large_readings = c.fetchall()

            if large_readings:
                print(f"Largest reading sizes: {[f'{size} chars' for (size,) in large_readings]}")

            conn.close()

        except Exception as e:
            print(f"Database analysis failed: {e}")

    def generate_report(self):
        """Generate performance report"""
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)

        uptime = time.time() - self.start_time
        print(f"Monitoring duration: {uptime:.1f} seconds")

        # Memory usage
        if self.metrics['memory_usage']:
            memory_values = [m['value'] for m in self.metrics['memory_usage']]
            print(f"Memory usage: avg={sum(memory_values)/len(memory_values):.1f}%, max={max(memory_values):.1f}%")

        # CPU usage
        if self.metrics['cpu_usage']:
            cpu_values = [c['value'] for c in self.metrics['cpu_usage']]
            print(f"CPU usage: avg={sum(cpu_values)/len(cpu_values):.1f}%, max={max(cpu_values):.1f}%")

        # Database performance
        if self.metrics['db_query_times']:
            query_times = [q['value'] for q in self.metrics['db_query_times']]
            print(f"DB query times: avg={sum(query_times)/len(query_times):.1f}ms, max={max(query_times):.1f}ms")

        # Alerts
        if self.alerts:
            print(f"\nAlerts generated: {len(self.alerts)}")
            recent_alerts = [a for a in self.alerts if a['timestamp'] > datetime.now() - timedelta(hours=1)]
            if recent_alerts:
                print("Recent alerts:")
                for alert in recent_alerts[-5:]:  # Last 5 alerts
                    print(f"  {alert['timestamp'].strftime('%H:%M:%S')} - {alert['message']}")
        else:
            print("\n✓ No performance alerts")

    def save_metrics(self, filename="performance_metrics.json"):
        """Save metrics to file"""
        try:
            # Convert deque to list and timestamps to strings for JSON serialization
            metrics_data = {}
            for key, value in self.metrics.items():
                if isinstance(value, deque):
                    metrics_data[key] = list(value)
                else:
                    metrics_data[key] = value

            # Convert timestamps to strings
            for metric_list in ['memory_usage', 'cpu_usage', 'db_query_times', 'response_times']:
                if metric_list in metrics_data:
                    for item in metrics_data[metric_list]:
                        if 'timestamp' in item:
                            item['timestamp'] = datetime.fromtimestamp(item['timestamp']).isoformat()

            # Convert alert timestamps
            alerts_data = []
            for alert in self.alerts:
                alert_copy = alert.copy()
                alert_copy['timestamp'] = alert['timestamp'].isoformat()
                alerts_data.append(alert_copy)

            data = {
                'metrics': metrics_data,
                'alerts': alerts_data,
                'generated_at': datetime.now().isoformat()
            }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"Metrics saved to {filename}")

        except Exception as e:
            print(f"Failed to save metrics: {e}")

def main():
    """Main performance monitoring function"""
    if len(sys.argv) < 2:
        print("Usage: python performance_monitor.py <command> [options]")
        print("\nCommands:")
        print("  monitor [interval]     - Start real-time monitoring (default interval: 5s)")
        print("  profile [operations]   - Run performance profiling (default: 100 operations)")
        print("  analyze               - Analyze database and system performance")
        print("  report                - Generate performance report")
        print("\nExamples:")
        print("  python performance_monitor.py monitor 10")
        print("  python performance_monitor.py profile 200")
        print("  python performance_monitor.py analyze")
        return

    command = sys.argv[1].lower()

    # Initialize monitor
    monitor = PerformanceMonitor()

    if command == "monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        try:
            monitor.start_monitoring(interval)
            print("Press Ctrl+C to stop monitoring...")

            while True:
                time.sleep(10)
                monitor.generate_report()

        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            monitor.stop_monitoring()
            monitor.generate_report()
            monitor.save_metrics()

    elif command == "profile":
        num_ops = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        print(f"Running performance profiling with {num_ops} operations...")

        monitor.profile_user_operations(num_ops)
        monitor.profile_iching_operations(num_ops)
        monitor.analyze_database_size()

    elif command == "analyze":
        print("Analyzing system and database performance...")
        monitor.analyze_database_size()

        # Quick system check
        print(f"\nSystem Information:")
        print(f"CPU count: {psutil.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print(f"Current memory usage: {psutil.virtual_memory().percent:.1f}%")
        print(f"Current CPU usage: {psutil.cpu_percent(interval=1):.1f}%")

    elif command == "report":
        print("Generating performance report...")
        monitor.generate_report()

    else:
        print(f"Unknown command: {command}")
        print("Use 'python performance_monitor.py' for usage information")

if __name__ == '__main__':
    main()
