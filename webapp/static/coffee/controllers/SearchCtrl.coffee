SearchCtrl = ($scope, $routeParams, Search, Currency)->
    
    $scope.search     = Search
    $scope.currencies = Currency
    # Watch for route change to update the search
    $scope.$watch $routeParams, ->
        # Update the query property of search according q 
        $scope.search.set($routeParams.q, $routeParams.c) if $routeParams.q?

    # Get the filtered result 
    # (no filter yet)
    $scope.userFilter = (d)-> true
    # True if the given value is the equivalent of the query
    $scope.isEquivalent = (d)-> Math.abs(d.current_value_usd  - $scope.search.query_usd) < 10
    # Event triggered when we click on a point
    $scope.pointSelection = (d)-> $scope.preview.id = d.id
    # Showed equivalent
    $scope.preview = id: 84

SearchCtrl.$inject = ['$scope', '$routeParams', 'Search', 'Currency'];