tell application "Warp"
    activate
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- New window
            keystroke "n" using {command down}
            delay 2
            
            -- Type tmux attach command
            keystroke "tmux attach -t cable_backend"
            keystroke return
            delay 1
            
            -- Split horizontally
            keystroke "d" using {command down, shift down}
            delay 1
            
            -- Attach to frontend
            keystroke "tmux attach -t cable_frontend"
            keystroke return
        end tell
    end tell
end tell