# Music Streaming Application

The **Music Streaming Application** is a versatile platform designed to cater to both music enthusiasts and creators. This application allows users to explore, upload, and manage music content seamlessly. Built on the Flask framework, it incorporates technologies such as Bootstrap for frontend development and SQLAlchemy for database interactions, providing a robust environment for discovering, uploading, and managing music tracks and albums.

## Technologies Used

- **Python**: The base programming language used to develop controllers, APIs, and other functionalities.
- **Flask**: A lightweight web framework for backend development.
  - **Flask_SQLAlchemy**: A Flask extension that provides tools and methods to interact with databases using SQLAlchemy.
  - **Flask_Login**: A Flask extension for implementing login functionality.
- **HTML**: Used to structure the webpages of the application.
- **Bootstrap**: Utilized for creating responsive pages and basic CSS styling.
- **Jinja2**: A templating engine used in conjunction with HTML for dynamic content rendering.
- **Werkzeug.security**: Used for secure password hashing.

## API Design

The application features a RESTful API that allows creators to manage songs on the platform. The API supports operations such as retrieving, uploading, updating, and deleting songs, as well as fetching information about all available songs.

## Architecture and Features

The application is built using the **Model-View-Controller (MVC)** architecture, which separates database operations (Model), the rendering of HTML pages (View), and the handling of user input and business logic (Controller). This structure enhances the organization of code and facilitates easier maintenance and scalability.

### Key Features

- **User Authentication**: Secure account registration, login, and logout functionality.
- **Role-Based Access**: Different user roles, including 'user,' 'creator,' and 'admin,' each with specific privileges.
- **Search Functionality**: Users can search for songs, albums, and artists based on various criteria.
- **Creator Dashboard**: Personalized dashboard for creators to view total songs uploaded, average ratings, and total albums.
- **Content Management**: Creators can upload new songs and manage their existing uploads.
- **Playlist Management**: Users can create and manage playlists with their favorite songs.
- **Rating and Reviews**: Users can rate songs and provide reviews, which contribute to the average rating displayed on the creator dashboard.
- **Admin Dashboard**: A dedicated dashboard for admins to monitor app performance, manage users, creators, and songs, and handle content moderation tasks like blacklisting users or flagging songs.
