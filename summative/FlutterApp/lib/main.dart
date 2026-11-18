import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const EarlyWarningApp());
}

class EarlyWarningApp extends StatelessWidget {
  const EarlyWarningApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Academic Early Warning System',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0D47A1), // Deep academic blue
          brightness: Brightness.light,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.grey.shade50,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      home: const PredictionScreen(),
    );
  }
}

class PredictionScreen extends StatefulWidget {
  const PredictionScreen({super.key});

  @override
  State<PredictionScreen> createState() => _PredictionScreenState();
}

class _PredictionScreenState extends State<PredictionScreen> {
  // Master key used to validate all form fields simultaneously
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  // - Linux Desktop / Web: 'http://127.0.0.1:8000/predict'
  // - Android Emulator (AVD): 'http://10.0.2.2:8000/predict'
  static const String _apiUrl = 'https://your-service.onrender.com/predict';

  // 1. Controllers for the 5 numeric percentage inputs (0.0 - 100.0)
  final TextEditingController _attendanceController = TextEditingController();
  final TextEditingController _midtermController = TextEditingController();
  final TextEditingController _assignmentsController = TextEditingController();
  final TextEditingController _quizzesController = TextEditingController();
  final TextEditingController _projectsController = TextEditingController();

  // 2. Selected values for the 3 categorical dropdowns (matching FastAPI Literal types)
  String _internetAccess = 'Yes';
  String _familyIncome = 'Medium';
  String _parentEducation = 'High School';

  // Allowed dropdown options matching our Pydantic schema exactly
  final List<String> _internetOptions = ['Yes', 'No'];
  final List<String> _incomeOptions = ['Low', 'Medium', 'High'];
  final List<String> _educationOptions = [
    'None',
    'High School',
    "Bachelor's",
    "Master's",
    'PhD',
  ];

  // 3. State variables for tracking loading status, API prediction output, and errors
  bool _isLoading = false;
  double? _predictedScore;
  String? _riskStatus;
  String? _advisoryMessage;
  String? _errorMessage;

  @override
  void dispose() {
    // Always clean up controllers to prevent memory leaks
    _attendanceController.dispose();
    _midtermController.dispose();
    _assignmentsController.dispose();
    _quizzesController.dispose();
    _projectsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Temporary placeholder until we paste Step 4
    return const Scaffold(
      body: Center(child: Text('Step 2 Ready')),
    );
  }
}