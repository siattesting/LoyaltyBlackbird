# Overview

LoyaltyApp is a full-stack web application inspired by the Blackbird payment/loyalty system, designed specifically for African restaurants and convenience stores. The application enables merchants to issue loyalty points to customers through multiple channels (voucher codes, QR codes, and airdrops), while customers can earn, transfer, and redeem points. Built as a Progressive Web App (PWA) with offline-first capabilities, it provides a seamless mobile experience for both merchants and customers in African markets.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure
The application follows Flask's application factory pattern with modular blueprint organization:
- **auth** module handles user registration, login, and authentication
- **dashboard** module provides separate interfaces for merchants and customers
- **transactions** module manages point issuance, transfers, and redemptions
- **static** directory contains PWA assets, JavaScript, CSS, and service worker
- **templates** directory uses Jinja2 templates with a base template and modular partials

## Database Design
Uses SQLAlchemy 2.0 ORM with modern syntax (Mapped[] and mapped_column) and SQLite for the MVP phase:
- **User model** supports both merchant and customer types with points balance tracking
- **Transaction model** handles all point movements with enum-based transaction types
- **Voucher model** (referenced but not fully implemented) for voucher code management
- Relationships use modern SQLAlchemy syntax with List[] type hints

## Authentication & Authorization
Implements Flask-Login for session management:
- Role-based access control distinguishing merchants from customers
- Password hashing using Werkzeug security utilities
- Login required decorators protect sensitive routes
- User type determines available features and dashboard views

## Frontend Architecture
Progressive Web App built with:
- **Pico.css** as the base CSS framework with African-inspired color customizations
- **Service Worker** for offline functionality and caching strategies
- **Web App Manifest** for native app-like installation
- **QR Code functionality** for point transfers and voucher generation
- **Responsive design** optimized for mobile-first African market usage

## Point System Logic
Multi-channel point distribution system:
- **Voucher codes** - merchants generate redeemable codes for customers
- **QR codes** - real-time scanning for instant point transfers
- **Airdrops** - direct point transfers to specific customer accounts
- **Customer transfers** - peer-to-peer point sharing between users
- Transaction history with filtering, sorting, and date range capabilities

## PWA Features
Offline-first architecture includes:
- Background sync for form submissions when connectivity is restored
- Asset caching for core application functionality
- Install prompts for native app-like experience
- Mobile-optimized interface with touch-friendly controls

# External Dependencies

## Core Framework
- **Flask** - Python web framework with application factory pattern
- **Flask-SQLAlchemy** - Database ORM with SQLAlchemy 2.0 syntax
- **Flask-Login** - User session management and authentication

## Database
- **SQLite** - File-based database for MVP deployment (noted for potential PostgreSQL migration)
- **SQLAlchemy 2.0** - Modern ORM with type hints and improved query syntax

## Frontend Libraries
- **Pico.css** - Minimalist CSS framework served via CDN
- **QRCode libraries** - For generating and scanning QR codes (Python qrcode library)

## PWA Technologies
- **Service Worker API** - For offline functionality and background sync
- **Web App Manifest** - For PWA installation capabilities
- **Camera API** - For QR code scanning functionality

## Development Tools
- **Werkzeug** - WSGI utilities and security helpers for password hashing
- **ProxyFix** - Middleware for proper header handling in production deployments

## Deployment Infrastructure
- **Docker** - Containerization (Dockerfile and docker-compose.yml referenced)
- **Environment variables** - Configuration management for secrets and settings

Note: The application is designed to be database-agnostic and can be easily migrated from SQLite to PostgreSQL for production scaling.