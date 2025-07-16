import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'dart:ui';
import '../theme/design_system.dart';
/// Generated from PowerBuilder window w_mail_test
class w_mail_testScreen extends StatefulWidget {
  static const String routeName = '/w_mail_test';
  const w_mail_testScreen({
    Key? key,  }) : super(key: key);

  @override
  State<w_mail_testScreen> createState() => _w_mail_testScreenState();
}

class _w_mail_testScreenState extends State<w_mail_testScreen> {
  @override
  void initState() {
    super.initState();  }

  @override
  void dispose() {    super.dispose();
  }
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Apply glassmorphism to the entire screen for Liquid Glass aesthetic
    return Stack(
      children: [
        // Background gradient for glass effect
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: isDark
                  ? [
                      Color(0xFF1C1C1E),
                      Color(0xFF2C2C2E),
                      Color(0xFF1C1C1E),
                    ]
                  : [
                      Color(0xFFF2F2F7),
                      Color(0xFFFFFFFF),
                      Color(0xFFF2F2F7),
                    ],
            ),
          ),
        ),
        Scaffold(
          backgroundColor: Colors.transparent,      appBar: AppDesignSystem.glassAppBar(
        title: '',
        isDark: isDark,      ),      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppDesignSystem.space4),
          child: Center(child: Text('No controls defined')),
        ),
      ),
        ),
      ],
    );
  }
}