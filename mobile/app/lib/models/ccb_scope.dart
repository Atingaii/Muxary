enum CcbScope {
  view('view'),
  content('content'),
  focus('focus'),
  terminalInput('terminal_input'),
  notify('notify'),
  ask('ask'),
  lifecycle('lifecycle'),
  admin('admin');

  const CcbScope(this.wireName);

  final String wireName;

  static CcbScope? tryParse(String value) {
    final normalized = value.trim().replaceAll('-', '_');
    for (final scope in CcbScope.values) {
      if (scope.wireName == normalized) {
        return scope;
      }
    }
    return null;
  }

  static Set<CcbScope> parseMany(Iterable<Object?> values) {
    final result = <CcbScope>{};
    for (final value in values) {
      if (value == null) {
        continue;
      }
      final scope = CcbScope.tryParse(value.toString());
      if (scope != null) {
        result.add(scope);
      }
    }
    return result;
  }
}
