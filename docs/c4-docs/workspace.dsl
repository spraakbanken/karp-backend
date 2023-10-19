workspace "Karp Backend" {
    !docs docs
    
    model {
        sbAuth = softwareSystem "sb-auth" "Språkbanken's Auth service"

        user = person "User"
        admin = person "Admin"
        machine = person "Machine" "machine"

        backend = softwareSystem "karp-backend" {
            webApp = container "Web API"
            cliApp = container "karp-cli"

            group "application" {
                auth = container "karp.auth"
                lex = container "karp.lex"
                search = container "karp.search"
            }
            main = container "karp.main"

            group "infrastructure" {

                auth_infrastructure = container "karp.auth_infrastructure"
                lex_infrastructure = container "karp.lex_infrastructure"
                search_infrastructure = container "karp.search_infrastructure

                lex_database = container "MariaDB" "" "Relational database schema" "Database"
                search_database = container "ElasticSearch" "" "Document database schema" "Database"
            }
        }


        lexCore = softwareSystem "karp-lex-core" {
            commands = container "karp.lex_core.commands" {
                entry_commands = component "Entry Commands"
                resource_commands = component "Resource Commands"
                entry_repo_commands = component "Entry Repository Commands"
            }
            valueObjects = container "karp.lex_core.value_objects"
            dtos = container "karp.lex_core.dtos" "Data Transfer Objects"

        }

        /* Relations */
        user -> webApp "Uses"
        machine -> webApp "Uses"
        admin -> cliApp "Uses"

        webApp -> auth "Uses"
        webApp -> lex "Uses"
        webApp -> main "Uses"
        webApp -> search "Uses"

        cliApp -> lex "Uses"
        cliApp -> main "Uses"
        cliApp -> search "Uses"

        lex -> lexCore

        main -> auth_infrastructure "Uses"
        main -> lex_infrastructure "Uses"
        main -> search_infrastructure "Uses"

        auth_infrastructure -> auth "Implements"
        auth_infrastructure -> sbAuth "Uses"
        lex_infrastructure -> lex "Implements"
        lex_infrastructure -> lex_database "Uses"
        search_infrastructure -> search "Implements"
        search_infrastructure -> search_database "Uses"
    }

    views {
        systemContext backend "BackendSystemContext" "karp-backend" {
            include *
            autoLayout
        }

        container backend {
            include *
            autoLayout
        }

        component lex_infrastructure {
            include *
            autoLayout
        }

        systemContext lexCore "LexCoreSystemContext" "karp-lex-core" {
            include *
            autoLayout
        }

        container lexCore {
            include *
            autoLayout
        }

        component commands {
            include *
            autoLayout
        }

    
        /* Theme for views */
        themes default https://static.structurizr.com/themes/amazon-web-services-2022.04.30/theme.json https://raw.githubusercontent.com/practicalli/structurizr/main/themes/practicalli/theme.json
    }

}