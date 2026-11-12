/// A small, UI-agnostic reporting boundary shared by every gateway transport.
/// Reporting never retries the operation that produced an outcome; callers own
/// retry policy and may only refresh safe reads after recovery.
enum GatewayConnectionOperation {
  coreRead,
  dataRead,
  stream,
  terminal,
  mutation,
}

abstract interface class GatewayConnectionOutcomeReporter {
  void succeeded(GatewayConnectionOperation operation);

  void failed(GatewayConnectionOperation operation, Object error);
}

abstract interface class GatewayConnectionOutcomeReportable {
  set outcomeReporter(GatewayConnectionOutcomeReporter? reporter);
}
