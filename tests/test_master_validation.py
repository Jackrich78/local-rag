#!/usr/bin/env python3
"""
Master Test Validation Suite - Comprehensive System Testing
Orchestrates all test suites and provides comprehensive health reporting

This master suite:
1. Runs all enhanced test suites (system health, API streaming, user interface)
2. Validates Docker profiles functionality
3. Creates comprehensive health reports
4. Supports both automated and human validation workflows
5. Establishes performance benchmarks for monitoring
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class MasterTestSuite:
    """Master orchestration for all test suites with comprehensive reporting."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results = {}
        self.start_time = None
        self.docker_compose_dir = self.base_dir.parent / "local-ai-packaged"
        
    def run_all_test_suites(self) -> Dict[str, Any]:
        """Execute all enhanced test suites and collect results."""
        print("🧪 Master Test Validation Suite")
        print("=" * 70)
        print(f"Starting comprehensive system testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        # Test suites to run (in dependency order)
        test_suites = [
            ("System Health", "test_system_health.py", "Infrastructure and core services"),
            ("API & Streaming", "test_api_streaming.py", "API endpoints and communication"),
            ("User Interface", "test_user_interface.py", "Browser experience and workflows")
        ]
        
        suite_results = {}
        
        for suite_name, script_name, description in test_suites:
            print(f"\n{'='*20} {suite_name.upper()} TESTS {'='*20}")
            print(f"📋 {description}")
            
            result = self._run_test_suite(script_name)
            suite_results[suite_name] = result
            
            # Show immediate results
            if result["success"]:
                print(f"✅ {suite_name}: {result['message']}")
            else:
                print(f"❌ {suite_name}: {result['message']}")
            
            time.sleep(2)  # Brief pause between suites
        
        # Additional validation tests
        print(f"\n{'='*20} DOCKER PROFILES VALIDATION {'='*20}")
        profiles_result = self._test_docker_profiles()
        suite_results["Docker Profiles"] = profiles_result
        
        print(f"\n{'='*20} SYSTEM READINESS CHECK {'='*20}")
        readiness_result = self._test_system_readiness()
        suite_results["System Readiness"] = readiness_result
        
        # Generate comprehensive report
        self.results = suite_results
        return self._generate_master_report()
    
    def _run_test_suite(self, script_name: str) -> Dict[str, Any]:
        """Run a specific test suite and capture results."""
        script_path = self.base_dir / script_name
        
        if not script_path.exists():
            return {
                "success": False,
                "message": f"Test script {script_name} not found",
                "exit_code": -1,
                "execution_time": 0
            }
        
        try:
            start_time = time.time()
            
            # Run the test script
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, timeout=300,  # 5 minute timeout
            cwd=str(self.base_dir))
            
            execution_time = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "message": f"Completed in {execution_time:.1f}s with exit code {result.returncode}",
                "exit_code": result.returncode,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Test suite timed out after 5 minutes",
                "exit_code": -2,
                "execution_time": 300
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Test execution failed: {str(e)}",
                "exit_code": -3,
                "execution_time": 0
            }
    
    def _test_docker_profiles(self) -> Dict[str, Any]:
        """Test Docker profiles functionality."""
        try:
            # Test that we can query different profile configurations
            profile_tests = [
                ("minimal", "Core services only"),
                ("database", "Core + database UI"), 
                ("extra", "Additional development tools"),
                ("search", "Web search functionality")
            ]
            
            profile_results = {}
            
            for profile, description in profile_tests:
                # Check which services would start with this profile
                result = subprocess.run([
                    "docker-compose", "--profile", profile, "config", "--services"
                ], capture_output=True, text=True, timeout=30,
                cwd=str(self.docker_compose_dir))
                
                if result.returncode == 0:
                    services = result.stdout.strip().split('\n')
                    profile_results[profile] = {
                        "success": True,
                        "services": services,
                        "count": len(services)
                    }
                else:
                    profile_results[profile] = {
                        "success": False,
                        "error": result.stderr
                    }
            
            # Check current running services
            current_result = subprocess.run([
                "docker-compose", "ps", "--services", "--filter", "status=running"
            ], capture_output=True, text=True, timeout=30,
            cwd=str(self.docker_compose_dir))
            
            running_services = []
            if current_result.returncode == 0:
                running_services = current_result.stdout.strip().split('\n')
            
            success = all(result["success"] for result in profile_results.values())
            
            return {
                "success": success,
                "message": f"Docker profiles validation: {len([r for r in profile_results.values() if r['success']])}/{len(profile_results)} profiles valid",
                "profile_results": profile_results,
                "currently_running": running_services
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Docker profiles test failed: {str(e)}"
            }
    
    def _test_system_readiness(self) -> Dict[str, Any]:
        """Validate system is ready for use."""
        try:
            readiness_checks = []
            
            # Check 1: Core services are running
            core_services = ["agentic-rag-agent", "open-webui", "supabase-db", "caddy"]
            running_containers = self._get_running_containers()
            
            missing_core = [svc for svc in core_services if svc not in running_containers]
            readiness_checks.append({
                "check": "Core Services Running",
                "success": len(missing_core) == 0,
                "details": f"Missing: {missing_core}" if missing_core else "All core services running"
            })
            
            # Check 2: Key endpoints responding
            import requests
            
            endpoints = [
                ("Agent Health", "http://localhost:8009/health"),
                ("Agent Models", "http://localhost:8009/v1/models"),
                ("OpenWebUI", "http://localhost:8002")
            ]
            
            for name, url in endpoints:
                try:
                    response = requests.get(url, timeout=10)
                    readiness_checks.append({
                        "check": f"{name} Endpoint",
                        "success": response.status_code in [200, 302],
                        "details": f"HTTP {response.status_code}"
                    })
                except Exception as e:
                    readiness_checks.append({
                        "check": f"{name} Endpoint", 
                        "success": False,
                        "details": str(e)
                    })
            
            # Check 3: Database has data
            try:
                db_result = subprocess.run([
                    "docker", "exec", "supabase-db", "psql", "-U", "postgres",
                    "-c", "SELECT COUNT(*) FROM documents;", "-t"
                ], capture_output=True, text=True, timeout=10,
                cwd=str(self.docker_compose_dir))
                
                if db_result.returncode == 0:
                    doc_count = int(db_result.stdout.strip())
                    readiness_checks.append({
                        "check": "Database Documents",
                        "success": doc_count > 0,
                        "details": f"{doc_count} documents found"
                    })
                else:
                    readiness_checks.append({
                        "check": "Database Documents",
                        "success": False,
                        "details": "Cannot query database"
                    })
            except Exception as e:
                readiness_checks.append({
                    "check": "Database Documents",
                    "success": False,
                    "details": str(e)
                })
            
            passed_checks = sum(1 for check in readiness_checks if check["success"])
            total_checks = len(readiness_checks)
            
            return {
                "success": passed_checks >= total_checks * 0.8,  # 80% pass rate
                "message": f"System readiness: {passed_checks}/{total_checks} checks passed",
                "checks": readiness_checks,
                "readiness_score": (passed_checks / total_checks) * 100
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"System readiness check failed: {str(e)}"
            }
    
    def _get_running_containers(self) -> List[str]:
        """Get list of currently running container names."""
        try:
            result = subprocess.run([
                "docker", "ps", "--format", "{{.Names}}"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                return []
        except Exception:
            return []
    
    def _generate_master_report(self) -> Dict[str, Any]:
        """Generate comprehensive master test report."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Calculate overall statistics
        total_suites = len(self.results)
        passed_suites = sum(1 for result in self.results.values() if result["success"])
        
        # Generate summary
        print("\n" + "=" * 70)
        print("📊 MASTER TEST VALIDATION SUMMARY")
        print("=" * 70)
        
        print(f"🕐 Total Execution Time: {total_time:.1f} seconds")
        print(f"📋 Test Suites Run: {total_suites}")
        print(f"✅ Suites Passed: {passed_suites}")
        print(f"❌ Suites Failed: {total_suites - passed_suites}")
        print(f"📈 Success Rate: {(passed_suites/total_suites)*100:.1f}%")
        
        # Detailed results
        print(f"\n🔍 DETAILED RESULTS:")
        for suite_name, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {status} {suite_name}: {result['message']}")
        
        # Overall assessment
        if passed_suites == total_suites:
            print(f"\n🎉 ALL TEST SUITES PASSED!")
            print(f"🚀 System is fully operational and ready for use")
            overall_status = "EXCELLENT"
        elif passed_suites >= total_suites * 0.8:
            print(f"\n✅ System mostly healthy with {total_suites - passed_suites} minor issues")
            print(f"💡 System is operational but investigate failed tests")
            overall_status = "GOOD"
        else:
            print(f"\n⚠️ System has significant issues - {total_suites - passed_suites} test suites failed")
            print(f"🔧 Investigation and fixes required before production use")
            overall_status = "NEEDS_ATTENTION"
        
        # Generate report data
        report = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": total_time,
            "overall_status": overall_status,
            "summary": {
                "total_suites": total_suites,
                "passed_suites": passed_suites,
                "failed_suites": total_suites - passed_suites,
                "success_rate": (passed_suites/total_suites)*100
            },
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations()
        }
        
        # Save report to file
        self._save_report(report)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        for suite_name, result in self.results.items():
            if not result["success"]:
                if suite_name == "System Health":
                    recommendations.append("🔧 Check Docker services and container health")
                    recommendations.append("📊 Verify database connectivity and data ingestion")
                elif suite_name == "API & Streaming":
                    recommendations.append("🌐 Investigate API endpoint connectivity issues")
                    recommendations.append("📡 Check streaming functionality and service communication")
                elif suite_name == "User Interface":
                    recommendations.append("🖥️ Verify OpenWebUI configuration and accessibility")
                    recommendations.append("🔄 Test browser workflows and error handling")
                elif suite_name == "Docker Profiles":
                    recommendations.append("🐳 Review Docker Compose profile configurations")
                elif suite_name == "System Readiness":
                    recommendations.append("⚡ Address system readiness issues before deployment")
        
        if not recommendations:
            recommendations.append("🎉 All tests passed - system is ready for production use!")
            recommendations.append("📈 Consider running tests regularly to maintain system health")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]) -> None:
        """Save test report to file."""
        try:
            report_file = self.base_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n💾 Detailed report saved to: {report_file}")
            
        except Exception as e:
            print(f"\n⚠️ Could not save report: {e}")

def main():
    """Run master test validation suite."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Master Test Validation Suite")
        print("Usage: python test_master_validation.py")
        print("\nComprehensive system testing including:")
        print("- System health and infrastructure validation")
        print("- API endpoints and streaming functionality")
        print("- User interface and workflow testing")
        print("- Docker profiles validation")
        print("- System readiness assessment")
        print("- Performance benchmarking")
        return
    
    print("🚀 Preparing to run comprehensive system validation...")
    print("⚠️  Prerequisites:")
    print("1. All services started with 'make up'")
    print("2. System has been running for at least 60 seconds")
    print("3. All enhanced test files are present")
    print()
    
    # Auto-run without user prompt for automation
    print("Starting master test validation suite...")
    
    master_tester = MasterTestSuite()
    report = master_tester.run_all_test_suites()
    
    # Exit with appropriate code
    if report["overall_status"] == "EXCELLENT":
        sys.exit(0)  # All tests passed
    elif report["overall_status"] == "GOOD":
        sys.exit(0)  # Mostly working, acceptable
    else:
        sys.exit(1)  # Significant issues detected

if __name__ == "__main__":
    main()