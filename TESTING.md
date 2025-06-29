# Testing and Performance Guide

This guide covers testing and performance monitoring for The Oracle I Ching App.

## Quick Start

### 1. Install Testing Dependencies
```bash
pip install -r requirements-test.txt
```

### 2. Run All Tests
```bash
python run_tests.py
```

### 3. Run Tests with Coverage
```bash
python run_tests.py --coverage
```

### 4. Run Performance Profiling
```bash
python run_tests.py --profile
```

## Test Structure

### Unit Tests
- `tests/test_user.py` - User model tests
- `tests/test_history.py` - History model tests
- `tests/test_iching.py` - I Ching logic tests

### Integration Tests
- `tests/test_app.py` - Flask application tests

### Performance Tests
- Built into each test file
- Dedicated performance monitoring script

## Running Individual Test Files

```bash
# Run specific test file
python -m unittest tests.test_user

# Run specific test class
python -m unittest tests.test_user.TestUser

# Run specific test method
python -m unittest tests.test_user.TestUser.test_user_creation
```

## Performance Monitoring

### Real-time Monitoring
```bash
# Start monitoring with 5-second intervals
python performance_monitor.py monitor 5

# Stop with Ctrl+C
```

### Performance Profiling
```bash
# Profile 100 operations of each type
python performance_monitor.py profile 100

# Profile 500 operations
python performance_monitor.py profile 500
```

### Database Analysis
```bash
python performance_monitor.py analyze
```

## Test Coverage

Coverage reports are generated in:
- Console output (when using `--coverage`)
- `htmlcov/` directory (HTML report)

To view HTML coverage report:
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## Performance Benchmarks

### Expected Performance Targets

**User Operations:**
- User creation: < 10ms per operation
- User retrieval: < 5ms per operation
- User authentication: < 15ms per operation

**I Ching Operations:**
- Hexagram casting: < 5ms per operation
- Text retrieval: < 20ms per operation

**Database Operations:**
- Simple queries: < 10ms
- Complex queries: < 50ms

**System Resources:**
- Memory usage: < 50MB for basic operations
- CPU usage: < 10% during normal operation

### Performance Alerts

The monitoring system will alert on:
- Memory usage > 80%
- CPU usage > 80%
- Database queries > 100ms
- Any operation taking > 1 second

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure you're running from the project root
cd /path/to/the-oracle
python run_tests.py
```

**2. Database Errors**
```bash
# Ensure data directory exists
mkdir -p data
```

**3. Missing Dependencies**
```bash
# Install all dependencies
pip install -r requirements-test.txt
```

### Performance Issues

**1. Slow Database Operations**
- Check database size: `python performance_monitor.py analyze`
- Consider adding indexes for large datasets
- Monitor for long-running queries

**2. High Memory Usage**
- Profile memory usage: `python performance_monitor.py monitor`
- Check for memory leaks in long-running processes
- Consider lazy loading for large datasets

**3. Slow I Ching Operations**
- Profile text parsing performance
- Consider caching frequently accessed hexagrams
- Optimize text processing algorithms

## Continuous Integration

### GitHub Actions (Example)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    - name: Run tests
      run: python run_tests.py --coverage
```

## Best Practices

### Writing Tests
1. **Test Names**: Use descriptive names that explain what is being tested
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Isolation**: Each test should be independent
4. **Coverage**: Aim for >90% code coverage
5. **Performance**: Include performance assertions in critical paths

### Performance Testing
1. **Baseline**: Establish performance baselines early
2. **Monitoring**: Set up continuous monitoring in production
3. **Alerts**: Configure alerts for performance degradation
4. **Profiling**: Regular profiling to identify bottlenecks
5. **Optimization**: Profile before and after optimizations

### Database Testing
1. **Isolation**: Use temporary databases for tests
2. **Cleanup**: Always clean up test data
3. **Performance**: Test with realistic data volumes
4. **Transactions**: Test transaction handling
5. **Concurrency**: Test concurrent access patterns

## Advanced Testing

### Load Testing
For production load testing, consider:
- Apache Bench (ab)
- wrk
- Locust
- Artillery

### Browser Testing
For UI testing:
- Selenium WebDriver
- Playwright
- Cypress

### API Testing
For API endpoint testing:
- Postman/Newman
- pytest with requests
- curl scripts

## Metrics and KPIs

### Key Metrics to Track
- Response time (95th percentile)
- Error rate
- Throughput (requests/second)
- Database query performance
- Memory usage
- CPU usage
- User satisfaction scores

### Performance Dashboards
Consider setting up dashboards with:
- Grafana + Prometheus
- New Relic
- DataDog
- Custom monitoring solutions
