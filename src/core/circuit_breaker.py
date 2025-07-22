"""Circuit breaker pattern implementation for fault tolerance."""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

    class CircuitBreakerConfig:
        pass
    """Configuration for circuit breaker."""

    # Failure threshold before opening circuit
    failure_threshold: int = 5

    # Success threshold to close circuit from half-open
    success_threshold: int = 2

    # Time to wait before trying half-open state (seconds)
    timeout: float = 60.0

    # Exception types to catch (None means catch all)
    expected_exceptions: tuple[type[Exception], ...] | None = None

    # Exceptions that should not trigger the circuit breaker
    excluded_exceptions: tuple[type[Exception], ...] | None = None

    # Optional callback when state changes
    on_state_change: Callable[[CircuitState, CircuitState], None] | None = None

    class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    total_calls: int = 0
    rejected_calls: int = 0
    state_changes: list = field(default_factory=list)

    class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(
        self,
        message: str,
        last_failure_time: float | None = None) -> None:
        super().__init__(message)
        self.last_failure_time = last_failure_time

        class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._half_open_start = None

    def _should_catch_exception(self, exception: Exception) -> bool:
    """Check if exception should trigger circuit breaker."""
        # Check excluded exceptions first
        if self.config.excluded_exceptions:
        if isinstance(exception, self.config.excluded_exceptions):
        return False
        return False

        # Check expected exceptions
        if self.config.expected_exceptions:
        return isinstance(exception, self.config.expected_exceptions)

        # Catch all exceptions by default
        return True

    def _change_state(self, new_state: CircuitState) -> None:
    """Change circuit breaker state."""
        if self.state != new_state:
        old_state = self.state
        self.state = new_state
        self.stats.state_changes.append(
        {"from": old_state, "to": new_state, "timestamp": datetime.now()}
        )

        if self.config.on_state_change:
        self.config.on_state_change(old_state, new_state)

    def _handle_success(self) -> None:
    """Handle successful call."""
        with self._lock:
        Any
        self.stats.success_count += 1
        self.stats.last_success_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
        if self.stats.success_count >= self.config.success_threshold:
        # Enough successes, close the circuit
        self._change_state(CircuitState.CLOSED)
        self.stats.failure_count = 0
        self.stats.success_count = 0
        elif self.state == CircuitState.CLOSED:
        # Reset failure count on success in closed state
        self.stats.failure_count = 0

    def _handle_failure(self, _exception: Exception) -> None:
    """Handle failed call."""
        with self._lock:
        Any
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
        if self.stats.failure_count >= self.config.failure_threshold:
        # Too many failures, open the circuit
        self._change_state(CircuitState.OPEN)
        elif self.state == CircuitState.HALF_OPEN:
        # Failure in half-open state, reopen the circuit
        self._change_state(CircuitState.OPEN)
        self.stats.success_count = 0

    def _should_attempt_reset(self) -> bool:
    """Check if we should try to reset the circuit."""
        return (
        self.state == CircuitState.OPEN
        and self.stats.last_failure_time is not None
        and time.time() - self.stats.last_failure_time >= self.config.timeout
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
    """Call function through circuit breaker.

        Args:
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments

        Returns:
        Function result

        Raises:
        CircuitBreakerError: If circuit is open
        Exception: If function raises exception
    """
        with self._lock:
        Any
        self.stats.total_calls += 1

        # Check if circuit should transition to half-open
        if self._should_attempt_reset():
        self._change_state(CircuitState.HALF_OPEN)
        self.stats.success_count = 0
        self._half_open_start = time.time()

        # Reject call if circuit is open
        if self.state == CircuitState.OPEN:
        self.stats.rejected_calls += 1
        raise CircuitBreakerError(
        f"Circuit breaker is OPEN (failures: {
        self.stats.failure_count})", self.stats.last_failure_time, )

        # Execute the function
        try:
        result = func(*args, **kwargs)
        self._handle_success()
        return result
        except Exception as e:
        if self._should_catch_exception(e):
        self._handle_failure(e)
        raise

    def reset(self) -> None:
    """Reset circuit breaker to closed state."""
        with self._lock:
        Any
        self._change_state(CircuitState.CLOSED)
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self._half_open_start = None

    def get_state(self) -> CircuitState:
    """Get current circuit state."""
        return self.state

    def get_stats(self) -> dict:
    """Get circuit breaker statistics."""
        return {
        "state": self.state.value,
        "failure_count": self.stats.failure_count,
        "success_count": self.stats.success_count,
        "total_calls": self.stats.total_calls,
        "rejected_calls": self.stats.rejected_calls,
        "last_failure_time": self.stats.last_failure_time,
        "last_success_time": self.stats.last_success_time,
        "state_changes": len(self.stats.state_changes),
        }

    def __call__(self, func: Callable) -> Callable:
        """Use as a decorator."""
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)
        
        # Attach circuit breaker instance for introspection
        wrapper.circuit_breaker = self
        return wrapper

def circuit_breaker(
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 60.0,
    expected_exceptions: tuple[type[Exception], ...] | None = None,
    excluded_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable], Callable]:
    """Decorator to add circuit breaker to a function.

    Args:
        failure_threshold: Failures before opening circuit
        success_threshold: Successes to close circuit
        timeout: Seconds before attempting reset
        expected_exceptions: Exception types to catch
        excluded_exceptions: Exception types to ignore

    Returns:
        Decorated function
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout=timeout,
        expected_exceptions=expected_exceptions,
        excluded_exceptions=excluded_exceptions,
    )

    breaker = CircuitBreaker(config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        # Attach circuit breaker instance for introspection
        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator


class CircuitBreakerManager:
    """Manage multiple circuit breakers."""

    def __init__(self) -> None:
    """Initialize circuit breaker manager."""
        self.breakers = {}
        self._lock = threading.Lock()

    def get_or_create(
        self, name: str, config: CircuitBreakerConfig | None = None
        ) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
        with self._lock:
        Any
        if name not in self.breakers:
        self.breakers[name] = CircuitBreaker(config)
        return self.breakers[name]

    def reset(self, name: str) -> None:
    """Reset a named circuit breaker."""
        with self._lock:
        Any
        if name in self.breakers:
        self.breakers[name].reset()

    def reset_all(self) -> None:
    """Reset all circuit breakers."""
        with self._lock:
        Any
        for breaker in self.breakers.values():
        breaker.reset()

    def get_stats(self) -> dict:
    """Get statistics for all circuit breakers."""
        with self._lock:
        return {
        name: breaker.get_stats() for name, breaker in self.breakers.items()
        }

    def get_open_circuits(self) -> list:
    """Get list of open circuit breakers."""
        with self._lock:
        Any
        return [
        name
        for name, breaker in self.breakers.items():
        if breaker.get_state() == CircuitState.OPEN:
        ]

        # Global circuit breaker manager
        _manager = CircuitBreakerManager()

    def get_circuit_breaker(
        name: str, config: CircuitBreakerConfig | None = None
        ) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
        return _manager.get_or_create(name, config)

    def reset_circuit_breaker(name: str) -> None:
    """Reset a named circuit breaker."""
        _manager.reset(name)

    def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers."""
        _manager.reset_all()
