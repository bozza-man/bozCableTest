#!/usr/bin/env python3

import sys
import time
import json
import getpass
from typing import Dict, Optional, List
from datetime import datetime

from security_monitor import SecurityMonitor
from ssh_manager import SSHManager
from usb_monitor import USBMonitor, USBEvent

class CableTester:
    def __init__(self):
        self.security_monitor = SecurityMonitor()
        self.ssh_manager = SSHManager()
        self.usb_monitor = USBMonitor(self.security_monitor)
        self.test_results = {}
        self.cable_authorized = False
        self.cable_hash = None
        
    def setup(self) -> bool:
        """Setup cable tester with remote Mac connection"""
        print("\n=== USB-C/Thunderbolt Cable Tester ===")
        print("\nThis tool will test cables between two Macs for:")
        print("1. Security threats (malicious cables)")
        print("2. Data transfer speeds")
        print("3. Power delivery capabilities")
        print("4. Thunderbolt functionality")
        print("5. Signal integrity\n")
        
        # Get SSH details
        print("Please provide SSH details for the remote Mac:")
        host = input("Remote host IP/hostname: ").strip()
        username = input("Remote username: ").strip()
        
        # Ask for authentication method
        auth_method = input("Authentication method (password/key) [key]: ").strip().lower()
        
        if auth_method == 'password':
            password = getpass.getpass("Password: ")
            connected = self.ssh_manager.connect(host, username, password=password)
        else:
            key_path = input("SSH key path (Enter for default): ").strip()
            connected = self.ssh_manager.connect(
                host, username, 
                key_path=key_path if key_path else None
            )
        
        if not connected:
            print("Failed to connect to remote Mac")
            return False
        
        print(f"Successfully connected to {host}")
        
        # Deploy remote agent
        print("Deploying remote agent...")
        if not self.ssh_manager.deploy_agent():
            print("Failed to deploy remote agent")
            return False
        
        # Start remote agent
        if not self.ssh_manager.start_remote_agent():
            print("Failed to start remote agent")
            return False
        
        print("Remote agent started successfully")
        
        # Capture baseline
        print("\nCapturing baseline USB state...")
        self.security_monitor.capture_baseline()
        
        # Setup USB monitor handlers
        self._setup_monitor_handlers()
        
        return True
    
    def _setup_monitor_handlers(self):
        """Setup USB monitor event handlers"""
        self.usb_monitor.register_handler(
            USBEvent.DEVICE_ADDED,
            self._handle_device_added
        )
        
        self.usb_monitor.register_handler(
            USBEvent.SUSPICIOUS_ACTIVITY,
            self._handle_suspicious_activity
        )
        
        self.usb_monitor.register_handler(
            USBEvent.ENUMERATION_FAILED,
            self._handle_enumeration_failed
        )
    
    def _handle_device_added(self, event: Dict):
        """Handle device addition event"""
        device = event['device']
        print(f"\nNew device detected: {device['name']}")
        print(f"VID: {device['vendor_id']}, PID: {device['product_id']}")
    
    def _handle_suspicious_activity(self, event: Dict):
        """Handle suspicious activity"""
        print("\n⚠️  SECURITY ALERT ⚠️")
        print(f"Suspicious activity detected!")
        for threat in event['threats']:
            print(f"  - {threat}")
        
        self.cable_authorized = False
    
    def _handle_enumeration_failed(self, event: Dict):
        """Handle enumeration failure"""
        print("\n⚠️  USB Enumeration Failed")
        print("This could indicate a malicious cable attempting to exploit the system")
    
    def run_security_test(self) -> bool:
        """Run security test on cable"""
        print("\n=== SECURITY TEST ===")
        print("Please connect the cable between the two Macs now.")
        print("Monitoring for cable insertion...")
        
        # Start USB monitoring
        self.usb_monitor.start_monitoring()
        
        # Wait for cable insertion
        cable_info = self.security_monitor.detect_cable_insertion(timeout=30)
        
        if not cable_info:
            print("No cable detected within timeout period")
            return False
        
        print(f"\nCable detected with {len(cable_info['new_devices'])} device(s)")
        
        # Analyze cable security
        print("Analyzing cable for security threats...")
        is_safe, threats = self.security_monitor.analyze_cable_security(cable_info)
        
        if is_safe:
            print("✅ Cable passed security checks")
            self.cable_hash = self.security_monitor.authorize_cable(cable_info)
            self.cable_authorized = True
            print(f"Cable authorized with hash: {self.cable_hash[:16]}...")
            
            self.test_results['security'] = {
                'status': 'PASSED',
                'authorized': True,
                'cable_hash': self.cable_hash,
                'timestamp': datetime.now().isoformat()
            }
            
            return True
        else:
            print("\n❌ CABLE FAILED SECURITY CHECKS")
            print("Threats detected:")
            for threat in threats:
                print(f"  - {threat}")
            
            self.test_results['security'] = {
                'status': 'FAILED',
                'authorized': False,
                'threats': threats,
                'timestamp': datetime.now().isoformat()
            }
            
            print("\n⚠️  DO NOT USE THIS CABLE ⚠️")
            print("The cable may contain malicious hardware.")
            
            return False
    
    def run_performance_tests(self):
        """Run performance tests on authorized cable"""
        if not self.cable_authorized:
            print("\nCable not authorized. Cannot run performance tests.")
            return
        
        print("\n=== PERFORMANCE TESTS ===")
        
        # Test data transfer speeds
        self._test_data_transfer()
        
        # Test power delivery
        self._test_power_delivery()
        
        # Test Thunderbolt functionality
        self._test_thunderbolt()
        
        # Test signal integrity
        self._test_signal_integrity()
    
    def _test_data_transfer(self):
        """Test data transfer speeds"""
        print("\n--- Data Transfer Test ---")
        
        test_sizes = [1, 10, 100]  # MB
        results = []
        
        for size_mb in test_sizes:
            print(f"Testing {size_mb}MB file transfer...")
            
            # Create test file on remote
            remote_file = self.ssh_manager.create_test_file(size_mb)
            if not remote_file:
                print(f"Failed to create {size_mb}MB test file")
                continue
            
            # Transfer file
            local_file = f"/tmp/cable_test_receive_{size_mb}MB.dat"
            start_time = time.time()
            
            success = self.ssh_manager.transfer_file(
                remote_file, local_file, direction='get'
            )
            
            transfer_time = time.time() - start_time
            
            if success:
                speed_mbps = (size_mb * 8) / transfer_time
                print(f"  Transfer speed: {speed_mbps:.2f} Mbps")
                results.append({
                    'size_mb': size_mb,
                    'time_seconds': transfer_time,
                    'speed_mbps': speed_mbps
                })
            else:
                print(f"  Transfer failed")
        
        # Determine USB generation based on speeds
        if results:
            avg_speed = sum(r['speed_mbps'] for r in results) / len(results)
            
            if avg_speed > 10000:  # 10 Gbps
                usb_gen = "USB4/Thunderbolt 3+"
            elif avg_speed > 5000:  # 5 Gbps
                usb_gen = "USB 3.2 Gen 2"
            elif avg_speed > 480:  # 480 Mbps
                usb_gen = "USB 3.0/3.1"
            else:
                usb_gen = "USB 2.0"
            
            print(f"\nDetected cable generation: {usb_gen}")
            
            self.test_results['data_transfer'] = {
                'status': 'COMPLETED',
                'results': results,
                'average_speed_mbps': avg_speed,
                'detected_generation': usb_gen
            }
    
    def _test_power_delivery(self):
        """Test USB Power Delivery"""
        print("\n--- Power Delivery Test ---")
        
        # Get power info from both machines
        local_power = self.security_monitor._get_ioreg_snapshot()
        remote_power = self.ssh_manager.monitor_power_delivery()
        
        if remote_power:
            print(f"Power delivery detected:")
            print(f"  Current: {remote_power.get('current_ma', 0)} mA")
            print(f"  Power State: {remote_power.get('power_state', 'Unknown')}")
            
            self.test_results['power_delivery'] = {
                'status': 'COMPLETED',
                'current_ma': remote_power.get('current_ma', 0),
                'power_state': remote_power.get('power_state', 0)
            }
        else:
            print("Could not determine power delivery capabilities")
            self.test_results['power_delivery'] = {
                'status': 'FAILED',
                'error': 'Could not retrieve power information'
            }
    
    def _test_thunderbolt(self):
        """Test Thunderbolt functionality"""
        print("\n--- Thunderbolt Test ---")
        
        tb_info = self.ssh_manager.check_thunderbolt_status()
        
        if tb_info and 'SPThunderboltDataType' in tb_info:
            tb_data = tb_info['SPThunderboltDataType']
            if tb_data:
                print("Thunderbolt connection detected")
                # Parse Thunderbolt info
                self.test_results['thunderbolt'] = {
                    'status': 'DETECTED',
                    'data': tb_data
                }
            else:
                print("No Thunderbolt connection detected")
                self.test_results['thunderbolt'] = {
                    'status': 'NOT_DETECTED'
                }
        else:
            print("Thunderbolt not available or not detected")
            self.test_results['thunderbolt'] = {
                'status': 'NOT_AVAILABLE'
            }
    
    def _test_signal_integrity(self):
        """Test signal integrity and error rates"""
        print("\n--- Signal Integrity Test ---")
        
        # Monitor for USB errors during a stress test
        print("Running signal integrity test (30 seconds)...")
        
        start_time = time.time()
        error_count = 0
        test_duration = 30
        
        # Create larger test file for stress testing
        test_file = self.ssh_manager.create_test_file(500)  # 500MB
        
        if test_file:
            # Transfer file multiple times
            iterations = 0
            while time.time() - start_time < test_duration:
                local_file = f"/tmp/signal_test_{iterations}.dat"
                success = self.ssh_manager.transfer_file(
                    test_file, local_file, direction='get'
                )
                
                if not success:
                    error_count += 1
                
                iterations += 1
                
                # Clean up local file
                self.ssh_manager.execute_command(f"rm -f {local_file}")
            
            error_rate = (error_count / iterations) * 100 if iterations > 0 else 0
            
            print(f"Completed {iterations} transfers")
            print(f"Error rate: {error_rate:.2f}%")
            
            self.test_results['signal_integrity'] = {
                'status': 'COMPLETED',
                'iterations': iterations,
                'errors': error_count,
                'error_rate_percent': error_rate
            }
        else:
            print("Failed to create test file for signal integrity test")
            self.test_results['signal_integrity'] = {
                'status': 'FAILED',
                'error': 'Could not create test file'
            }
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n\n=== CABLE TEST REPORT ===")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Security results
        security = self.test_results.get('security', {})
        print(f"\nSecurity Test: {security.get('status', 'NOT_RUN')}")
        if security.get('status') == 'FAILED':
            print("  Threats detected:")
            for threat in security.get('threats', []):
                print(f"    - {threat}")
        elif security.get('status') == 'PASSED':
            print(f"  Cable Hash: {security.get('cable_hash', '')[:16]}...")
        
        # Performance results
        if self.cable_authorized:
            # Data transfer
            data_transfer = self.test_results.get('data_transfer', {})
            if data_transfer.get('status') == 'COMPLETED':
                print(f"\nData Transfer Test: COMPLETED")
                print(f"  Average Speed: {data_transfer.get('average_speed_mbps', 0):.2f} Mbps")
                print(f"  Detected Generation: {data_transfer.get('detected_generation', 'Unknown')}")
            
            # Power delivery
            power = self.test_results.get('power_delivery', {})
            if power.get('status') == 'COMPLETED':
                print(f"\nPower Delivery Test: COMPLETED")
                print(f"  Current: {power.get('current_ma', 0)} mA")
            
            # Thunderbolt
            tb = self.test_results.get('thunderbolt', {})
            print(f"\nThunderbolt Test: {tb.get('status', 'NOT_RUN')}")
            
            # Signal integrity
            signal = self.test_results.get('signal_integrity', {})
            if signal.get('status') == 'COMPLETED':
                print(f"\nSignal Integrity Test: COMPLETED")
                print(f"  Error Rate: {signal.get('error_rate_percent', 0):.2f}%")
        
        # Save report to file
        report_file = f"cable_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        
        # Stop monitoring
        self.usb_monitor.stop_monitoring()
        
        # Stop remote agent
        self.ssh_manager.stop_remote_agent()
        
        # Disconnect SSH
        self.ssh_manager.disconnect()
        
        print("Cleanup complete")

def main():
    tester = CableTester()
    
    try:
        # Setup
        if not tester.setup():
            print("Setup failed. Exiting.")
            return 1
        
        # Run security test first
        if tester.run_security_test():
            # Only run performance tests if cable is safe
            
            continue_testing = input("\nCable is safe. Run performance tests? (y/n): ")
            if continue_testing.lower() == 'y':
                tester.run_performance_tests()
        
        # Generate report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        tester.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())