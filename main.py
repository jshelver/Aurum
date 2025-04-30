import ferium_wrapper

def main():
    # Example usage of the ferium_wrapper functions
    try:
        # List existing profiles
        profiles = ferium_wrapper.list_profiles()
        print("Existing profiles:", profiles)

        # # Create a new profile
        # new_profile = ferium_wrapper.create_profile("TestProfile", "1.16.5", "fabric")
        # print("Created profile:", new_profile)

        # # Switch to the new profile
        # switched_profile = ferium_wrapper.switch_profile("1.21.4")
        # print("Switched to profile:", switched_profile)

        # List mods in the active profile
        mods = ferium_wrapper.list_mods()
        print("Mods in active profile:", mods)

        # # Add mods to the active profile
        # added_mods = ferium_wrapper.add_mods(["mod1", "mod2"])
        # print("Added mods:", added_mods)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
