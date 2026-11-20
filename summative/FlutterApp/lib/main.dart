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
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  static const String _apiUrl = "https://student-academic-performance-checker.onrender.com/predict"; 

  // Controllers for the 5 numeric percentage inputs (0.0 - 100.0)
  final TextEditingController _attendanceController = TextEditingController();
  final TextEditingController _midtermController = TextEditingController();
  final TextEditingController _assignmentsController = TextEditingController();
  final TextEditingController _quizzesController = TextEditingController();
  final TextEditingController _projectsController = TextEditingController();

  // Selected values for the 3 categorical dropdowns (matching FastAPI Literal types)
  String _internetAccess = 'Yes';
  String _familyIncome = 'Medium';
  String _parentEducation = 'High School';

  // Allowed dropdown options matching our Pydantic schema
  final List<String> _internetOptions = ['Yes', 'No'];
  final List<String> _incomeOptions = ['Low', 'Medium', 'High'];
  final List<String> _educationOptions = [
    'None',
    'High School',
    "Bachelor's",
    "Master's",
    'PhD',
  ];

  // State variables for tracking loading status, API prediction output, and errors
  bool _isLoading = false;
  double? _predictedScore;
  String? _riskStatus;
  String? _advisoryMessage;
  String? _errorMessage;

  @override
  void dispose() {
    _attendanceController.dispose();
    _midtermController.dispose();
    _assignmentsController.dispose();
    _quizzesController.dispose();
    _projectsController.dispose();
    super.dispose();
  }
  // Validates that text inputs are not empty, are valid numbers, and fall within 0.0 - 100.0.
  String? _validatePercentage(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Required field';
    }
    final number = double.tryParse(value.trim());
    if (number == null) {
      return 'Enter a valid number';
    }
    if (number < 0.0 || number > 100.0) {
      return 'Must be 0.0 to 100.0';
    }
    return null; 
  }

  // Clears all text controllers, resets dropdowns to defaults, and hides results/errors.
  void _resetForm() {
    _formKey.currentState?.reset();
    _attendanceController.clear();
    _midtermController.clear();
    _assignmentsController.clear();
    _quizzesController.clear();
    _projectsController.clear();
    
    setState(() {
      _internetAccess = 'Yes';
      _familyIncome = 'Medium';
      _parentEducation = 'High School';
      _predictedScore = null;
      _riskStatus = null;
      _advisoryMessage = null;
      _errorMessage = null;
    });
  }

  //Packages the form data into JSON, sends it to FastAPI, and parses the response.
  Future<void> _predictScore() async {
    // 1. Trigger the _validatePercentage check on all 5 text fields
    if (!_formKey.currentState!.validate()) {
      return; // Stop immediately if any field is invalid
    }
    // Lock the UI by showing the loading spinner and clearing old results
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _predictedScore = null;
      _riskStatus = null;
      _advisoryMessage = null;
    });

    // Build the JSON payload using exactly the snake_case keys your Pydantic schema expects
    final Map<String, dynamic> payload = {
      "attendance": double.parse(_attendanceController.text.trim()),
      "midterm_score": double.parse(_midtermController.text.trim()),
      "assignments_avg": double.parse(_assignmentsController.text.trim()),
      "quizzes_avg": double.parse(_quizzesController.text.trim()),
      "projects_score": double.parse(_projectsController.text.trim()),
      "internet_access_at_home": _internetAccess,
      "family_income_level": _familyIncome,
      "parent_education_level": _parentEducation,
    };

    // Send the POST request to the API
    try {
      final response = await http.post(
        Uri.parse(_apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      );

      // Handle the API Response
      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          _predictedScore = responseData['predicted_total_score'];
          _riskStatus = responseData['risk_status'];
          _advisoryMessage = responseData['message'];
        });
      } else if (response.statusCode == 422) {
        setState(() {
          _errorMessage = "API Validation Error: Please check your input bounds.\nServer details: ${response.body}";
        });
      } else {
        setState(() {
          _errorMessage = "Server Error (${response.statusCode}):\n${response.body}";
        });
      }
    } catch (error) {
      setState(() {
        _errorMessage = "Network Error: Could not connect to the API. Check your internet connection and API URL.\nDetails: $error";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  
  //THE SCREEN LAYOUT AND UI COMPONENTS
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Early Warning System', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _resetForm,
            tooltip: 'Reset Form',
          )
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // HEADER CARD
                Card(
                  elevation: 0,
                  color: Theme.of(context).colorScheme.primaryContainer,
                  child: const Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Text(
                      "Enter the student's mid-semester progress using the metrics like attendance, mid term exam, so on  and socioeconomic indicators to predict their final score. ",
                      style: TextStyle(fontSize: 15),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // ACADEMIC METRICS SECTION
                const Text('Academic Performance (0 - 100)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const Divider(),
                _buildNumericField(_attendanceController, 'Attendance (%)', Icons.calendar_today),
                const SizedBox(height: 12),
                _buildNumericField(_midtermController, 'Midterm Score(0-100)', Icons.assignment),
                const SizedBox(height: 12),
                _buildNumericField(_assignmentsController, 'Assignments Average(0-100)', Icons.library_books),
                const SizedBox(height: 12),
                _buildNumericField(_quizzesController, 'Quizzes Average(0-100)', Icons.quiz),
                const SizedBox(height: 12),
                _buildNumericField(_projectsController, 'Projects Score(0-100)', Icons.science),
                const SizedBox(height: 24),

                // SOCIOECONOMIC INDICATORS SECTION
                const Text('Socioeconomic Context', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const Divider(),
                _buildDropdownField(
                  'Internet Access at Home',
                  _internetAccess,
                  _internetOptions,
                  (val) => setState(() => _internetAccess = val!),
                  Icons.wifi,
                ),
                const SizedBox(height: 12),
                _buildDropdownField(
                  'Family Income Level',
                  _familyIncome,
                  _incomeOptions,
                  (val) => setState(() => _familyIncome = val!),
                  Icons.attach_money,
                ),
                const SizedBox(height: 12),
                _buildDropdownField(
                  'Parent Education Level',
                  _parentEducation,
                  _educationOptions,
                  (val) => setState(() => _parentEducation = val!),
                  Icons.school,
                ),
                const SizedBox(height: 32),

                // ACTION BUTTON
                SizedBox(
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _predictScore,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      foregroundColor: Colors.white,
                      textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    child: _isLoading
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Text('Predict Final Score'),
                  ),
                ),
                const SizedBox(height: 24),

                // 5. RESULT & ERROR DISPLAY AREA
                if (_errorMessage != null)
                  Card(
                    color: Colors.red.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                if (_predictedScore != null) _buildResultCard(),
                
                const SizedBox(height: 40), // Bottom scroll padding
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Helper to build a clean numeric text input field
  Widget _buildNumericField(TextEditingController controller, String label, IconData icon) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Theme.of(context).colorScheme.primary),
      ),
      validator: _validatePercentage,
    );
  }

  //Helper to build a styled dropdown selector
  Widget _buildDropdownField(String label, String currentValue, List<String> options, ValueChanged<String?> onChanged, IconData icon) {
    return DropdownButtonFormField<String>(
      value: currentValue,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Theme.of(context).colorScheme.primary),
      ),
      items: options.map((String value) {
        return DropdownMenuItem<String>(
          value: value,
          child: Text(value),
        );
      }).toList(),
      onChanged: onChanged,
    );
  }

  // Helper to build the color-coded prediction result card
  Widget _buildResultCard() {
    // Determine badge color based on risk status
    Color statusColor = Colors.green;
    if (_riskStatus == 'High Risk') statusColor = Colors.red;
    if (_riskStatus == 'Moderate Risk') statusColor = Colors.orange;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            const Text('Predicted Final Score', style: TextStyle(fontSize: 16, color: Colors.grey)),
            const SizedBox(height: 8),
            Text(
              '${_predictedScore!.toStringAsFixed(2)} / 100',
              style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.primary),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
              child: Text(
                _riskStatus!,
                style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              _advisoryMessage!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 15, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }
}
