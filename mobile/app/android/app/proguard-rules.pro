# ML Kit registrars are named in Android manifest metadata and instantiated
# reflectively. Keep their no-argument constructors in optimized release APKs.
-keep class com.google.mlkit.** implements com.google.firebase.components.ComponentRegistrar {
    <init>();
}
