# Positives

This is the first code I've written in GO, so it's worth documenting the experience. 

In the same way I would recommend Python as "my first programming language", I would recommend Go as "my first statically typed programming language". 

It's easy to learn the basics within a few days and start writing.

It's easy to write, easy to get into a flow state and results come quickly.

In general, an excellent development experience within VSCode. 

All errors are clearly visible in the IDE before even attempting to compile.

Every line of unused code gets highlighted, every unused variable, every uncalled function, resulting in much cleaner code. 

All variables in the package scope are available without importing, making it quick and easy to separate out chunks of code into new files.

Multi-threading built in, and all the tools that make it easy to manage, like WaitGroups, Mutex locks, etc.

Structs and struct functions are cleaner, quicker and less abstract to write than Python or Javascript classes. 

It's rare to need anything outside of the core library, so far only an ORM called Gorm.

Compiles quickly to an executable binary which can run on any machine. 

The time package functions very simply and logically, something that Python could improve on.

It's blazing fast, finishing the deconstruction in 24 minutes compared to 24 hours for Python.


# Negatives

If doing lots of string manipulation with non-ASCII letters, you have to use []runes instead of strings, and [][]rune instead of []string , which introduces a slight initial bump in complexity.

It's not as intuitive as Python, you can't guess how to do something, but once you know the method and the syntax, it's no problem. 

