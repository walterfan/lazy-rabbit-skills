# Go Testing

Use this reference when writing or reviewing Go tests for handlers, services,
repositories, clients, or concurrent code.

## Default test style

- Prefer table-driven tests for business logic with multiple scenarios
- Use descriptive `t.Run(...)` case names
- Keep tests independent and isolated
- Cover happy path, edge cases, and error paths
- Use `require` for must-pass assertions and `assert` for the rest
- Mock external dependencies through small interfaces

## Typical structure

```go
func TestService_DoThing(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        setup   func(*MockRepo)
        wantErr bool
    }{
        {name: "success"},
        {name: "error when input missing", wantErr: true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockRepo := new(MockRepo)
            if tt.setup != nil {
                tt.setup(mockRepo)
            }

            svc := NewService(mockRepo)
            _, err := svc.DoThing(context.Background(), tt.input)

            if tt.wantErr {
                require.Error(t, err)
            } else {
                require.NoError(t, err)
            }

            mockRepo.AssertExpectations(t)
        })
    }
}
```

## What to cover

- Happy path behavior
- Empty, nil, and zero-value inputs
- Boundary values
- Dependency failures
- Validation failures
- Not-found vs internal-error branches
- Context cancellation or timeout when the code respects context
- Concurrency behavior for goroutines, workers, or caches

## Handler tests

- Validate status code, response body, and headers
- Confirm invalid input returns stable client errors
- Check that request context is passed into downstream calls when visible
- Avoid asserting on internal implementation details that do not change behavior

## Repository and client tests

- Verify parameterized query shape indirectly through behavior or mocks
- Check mapping of transport/database errors into stable service errors
- For Resty or HTTP client code, cover non-2xx responses and timeout/error paths

## Concurrency test notes

- Use `go test -race ./...` whenever shared state or goroutines changed
- Prefer deterministic coordination with channels or wait groups over `time.Sleep`
- Assert cleanup paths so workers do not outlive the test unnecessarily

## Quick checklist

- Exported behavior changed -> corresponding test added or updated
- Error path covered
- Edge case covered
- Mock expectations verified where interactions matter
- No brittle sleep-based timing if synchronization primitives can express intent
- Race detector considered for concurrent code
