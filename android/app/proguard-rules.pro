# Retrofit / Moshi / OkHttp keep rules
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations

-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response

# Moshi generated adapters + model classes
-keep class com.apex.os.data.model.** { *; }
-keepclassmembers class com.apex.os.data.model.** { *; }

# OkHttp platform warnings
-dontwarn okhttp3.internal.platform.**
-dontwarn org.conscrypt.**
