import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'core/config/app_config.dart';
import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';
import 'core/di/service_locator.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';
import 'features/companion/presentation/bloc/companion_bloc.dart';
import 'features/conversation/presentation/bloc/conversation_bloc.dart';
import 'features/proactive/presentation/bloc/proactive_bloc.dart';
import 'shared/services/notification_service.dart';
import 'shared/services/analytics_service.dart';
import 'shared/services/storage_service.dart';

final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = 
    FlutterLocalNotificationsPlugin();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  // Initialize Crashlytics
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
  PlatformDispatcher.instance.onError = (error, stack) {
    FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
    return true;
  };
  
  // Initialize services
  await setupServiceLocator();
  await StorageService.instance.init();
  await NotificationService.instance.init(flutterLocalNotificationsPlugin);
  
  // Initialize Analytics
  AnalyticsService.instance.init();
  
  // Configure GoRouter
  final router = AppRouter.createRouter();
  
  runApp(PAOApp(router: router));
}

class PAOApp extends StatelessWidget {
  final GoRouter router;
  
  const PAOApp({super.key, required this.router});
  
  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => sl<AuthBloc>()..add(AuthStarted())),
        BlocProvider(create: (_) => sl<CompanionBloc>()),
        BlocProvider(create: (_) => sl<ConversationBloc>()),
        BlocProvider(create: (_) => sl<ProactiveBloc>()),
      ],
      child: MaterialApp.router(
        title: 'PAO - Your AI Companion',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routerConfig: router,
        builder: (context, child) {
          return MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(
                MediaQuery.of(context).textScaler.scale(1.0).clamp(0.8, 1.3),
              ),
            ),
            child: child!,
          );
        },
      ),
    );
  }
}