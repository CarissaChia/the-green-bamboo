<!-- HTML -->
<template>
    <NavBar />

    <!-- Display when data is still loading -->
    <div class="text-info-emphasis fst-italic fw-bold fs-5 pt-5" v-if="dataLoaded == false">
        <span>Loading page, please wait...</span>
        <br><br>
        <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    </div>

    <!-- Display when data fails to load-->
    <div class="text-danger fst-italic fw-bold fs-3 pt-5" v-if="dataLoaded == null"> 
        <span>An error occurred while loading this page, please try again!</span>
        <br>
        <button class="btn primary-btn btn-sm" @click="this.$router.go(-1)">
            <span class="fs-5 fst-italic"> Return to previous page </span>
        </button>
        <button class="btn primary-btn btn-sm mx-1" @click="this.$router.go(0)">
            <span class="fs-5 fst-italic"> Go to Home page </span>
        </button>
    </div>

    <!-- [if] no search input -->
    <div v-if="search == false && dataLoaded == true">
        <!-- header -->
        <div class="container pt-5 mobile-view-hide">
            <div class="row">
                <!-- tagline -->
                <div class="col-8">
                    <h1 class="text-start" v-if="userID == ''"> What's Pouring? </h1>
                    <h1 class="text-start" v-else-if="userType == 'user'"> Hello, {{ displayName }}! What's Pouring? </h1>
                    <h1 class="text-start" v-else> Hello, {{ username }}! What's Pouring? </h1>
                </div>
                <!-- button -->
                <div v-if="!userID" class="col-4 text-end"  style="padding-right:40px;" >
                    <div class="d-grid gap-2">
                        <router-link :to="{ path: '/signUp' }">
                            <button class="btn secondary-btn-border-thick btn-lg" style="font-weight: bold;"> 
                                Sign Up to Start Pouring 
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-right" viewBox="0 0 16 16">
                                    <path fill-rule="evenodd" d="M1 8a.5.5 0 0 1 .5-.5h11.793l-3.147-3.146a.5.5 0 0 1 .708-.708l4 4a.5.5 0 0 1 0 .708l-4 4a.5.5 0 0 1-.708-.708L13.293 8.5H1.5A.5.5 0 0 1 1 8"/>
                                </svg>
                            </button>
                        </router-link>
                    </div>
                </div>
            </div>
        </div>

        <!-- main content -->
        <div class="container pt-3">
            <div class="row">
                <!-- left pane -->
                <div class="col-lg-3 col-md-4 col-12 mobile-view-hide">
                    <div class="container p-lg-0 p-md-0 p-4">
                        <!-- [user] your drinks shelf & brands you follow -->
                        <div v-if="userType == 'user' || userType == ''" class="row">
                            <!-- [moderator] listing requests -->
                            <div v-if="isAdmin || isModerator" class="col-12">
                                <div class="square primary-square-green-outline rounded p-3 mb-3">
                                    <!-- header text -->
                                    <div class="square-inline text-start">
                                        <span v-if="totalRequests != 0" class="square-inline text-start mr-auto">
                                            <h4>
                                                <span class="title-card-text"> {{ totalRequests }} </span> Pending Listing Requests 
                                            </h4>
                                        </span>
                                        <h4 v-else class="square-inline text-start mr-auto">  No New Pending Listing Requests! </h4>
                                    </div>
                                    <!-- body -->
                                    <div v-if="totalRequests != 0">
                                        <div style="align-items: center; justify-content: center;">
                                            <p>
                                                <span class="title-card-text"> {{ requestListings.length}} </span> New Listing Requests
                                                <br>
                                                <span class="title-card-text"> {{requestEdits.length}} </span> Edit Listing Requests
                                                <br>
                                                <span class="title-card-text"> {{requestDupes.length}} </span> Duplicate Reports
                                            </p>
                                            <router-link :to="{ path: '/request/view' }">
                                                <button class="btn secondary-btn-blue btn-sm py-2 px-3" style="font-weight: bold;"> View all requests </button>
                                            </router-link> <!-- TZH changed secondary-btn-border to secondary-btn-blue -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- your drinks shelf -->
                            <div class="col-12">
                                <div class="square primary-square-green rounded p-3 mb-3 text-start" style="height: 325px;">
                                    <!-- header text -->
                                    <div class="square-inline">
                                        <router-link :to="{ path: '/profile/user/'+userID }" class="reverse-clickable-text">
                                            <h4 class="square-inline text-start mr-auto reverse-clickable-text"> Your Drinks Shelf </h4>
                                        </router-link>
                                    </div>
                                    <!-- body -->
                                    <div style="height: 85%;">
                                        <!-- [if] drinks in drink shelf -->
                                        <div v-if="drinkShelf.length != 0" class="overflow-auto" style="max-height: 100%;">
                                            <div class="text-start mb-2" v-for="listing in drinkShelf" v-bind:key="listing.id">
                                                <div class="d-flex align-items-start">
                                                    <router-link :to="{ path: '/listing/view/' +listing.id}" class="reverse-clickable-text">
                                                        <img :src="(listing.photo || defaultProfilePhoto)" style="width: 70px; height: 70px;">
                                                    </router-link>
                                                    <span class="ms-3 reverse-clickable-text"> 
                                                        <router-link :to="{ path: '/listing/view/' +listing.id}" class="reverse-clickable-text">
                                                            <b> {{ listing.listingName }} </b> 
                                                        </router-link>
                                                        <br>
                                                        <router-link :to="{ path: '/profile/producer/' +listing.producerID}" class="reverse-clickable-text">
                                                        {{ getProducerName(listing) }}
                                                        </router-link>
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div v-if="userID && drinkShelf.length == 0" style="display: flex; align-items: center; justify-content: center; height: 100%;">
                                            <h6 class="fst-italic"> No drinks added yet. </h6>
                                        </div>
                                        <div v-else-if="!userID" style="display: flex; align-items: center; justify-content: center; height: 100%;">
                                            <router-link :to="{ path: '/login' }">
                                                <button class="btn secondary-btn-border-thick py-2 px-3" style="font-weight: bold;"> Log in to add a drink to shelf </button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- brands you follow -->
                            <div class="col-12">
                                <div class="square primary-square-green rounded p-3 mb-3 text-start" style="height: 325px;">
                                    <!-- header text -->
                                    <div class="square-inline">
                                        <h4 class="square-inline text-start mr-auto"> Brands You Follow </h4>
                                    </div>
                                    <!-- body -->
                                    <div style="height: 85%;">
                                        <div v-if="questionsUpdates.length > 0" class="overflow-auto" style="max-height: 100%;">
                                            <div v-for="(update, index) in questionsUpdates" :key="index">
                                                <!--Show if it's either producer or venue update-->
                                                <span v-if="update.type == 'producerUpdate' || update.type == 'venueUpdate'">
                                                        <router-link v-if="update.type == 'producerUpdate'" :to="{ path: '/profile/producer/' + update.id }" class="reverse-text">
                                                            <img :src="(update.photo || defaultProfilePhoto)" style="width: 35px; height: 35px;" class="img-border">
                                                            <b class="ps-2"> {{ update.name }} </b>
                                                        </router-link>
                                                        <router-link v-else :to="{ path: '/profile/venue/' + update.id }" class="reverse-text">
                                                            <img :src="(update.photo || defaultProfilePhoto)" style="width: 35px; height: 35px;" class="img-border">
                                                            <b class="ps-2"> {{ update.name }} </b>
                                                        </router-link>
                                                    <br/>
                                                    updated status: "<b>{{ update.text }}</b>"
                                                    <br>
                                                    <i>{{ getTimeDifference(update.date) }}</i>
                                                    <br><br>
                                                </span>

                                                <!-- Show if it's either producer or venue question? (Kai Lin wants to show newly added expressions)-->
                                            </div>
                                        </div>
                                        <div v-else-if="userID" style="display: flex; align-items: center; justify-content: center; height: 100%;">
                                            <h6 class="fst-italic"> No brands added yet. </h6>
                                        </div>
                                        <div v-else style="display: flex; align-items: center; justify-content: center; height: 100%;">
                                            <router-link :to="{ path: '/login' }">
                                                <button class="btn secondary-btn-border-thick btn-sm py-2 px-3" style="font-weight: bold;"> Log in to follow your favourite brands</button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- [producer] listing requests / fan questions / activity -->
                        <div v-else-if="userType == 'producer'" class="row">
                            <!-- listing requests -->
                            <div class="col-12"> 
                                <div class="square primary-square-green-outline rounded p-3 mb-3"> <!--tzh changed to green outline -->
                                    <!-- header text -->
                                    <div class="square-inline text-start">
                                        <span v-if="totalRequests != 0" class="square-inline text-start mr-auto">
                                            <h4>
                                                <span class="title-card-text"> {{ totalRequests }} </span> Pending Listing Requests 
                                            </h4>
                                        </span>
                                        <h4 v-else class="square-inline text-start mr-auto">  No New Pending Listing Requests! </h4>
                                    </div>
                                    <!-- body -->
                                    <div v-if="totalRequests != 0">
                                        <div style="align-items: center; justify-content: center;">
                                            <p>
                                                <span class="title-card-text"> {{ requestListings.length}} </span> New Listing Requests
                                                <br>
                                                <span class="title-card-text"> {{requestEdits.length}} </span> Edit Listing Requests
                                                <br>
                                                <span class="title-card-text"> {{requestDupes.length}} </span> Duplicate Reports
                                            </p>
                                            <router-link :to="{ path: '/request/view' }">
                                                <button class="btn secondary-btn-border btn-sm py-2 px-3" style="font-weight: bold;"> View all requests </button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- fan questions -->
                            <div class="col-12">
                                <div class="square primary-square-green-outline rounded p-3 mb-3">   <!--tzh changed to green outline -->
                                    <!-- header text -->
                                    <div class="square-inline">
                                        <span v-if="unansweredQuestions.length != 0" class="square-inline text-start mr-auto">
                                            <h4>
                                                <span class="title-card-text"> {{ unansweredQuestions.length }} </span>  Pending Fan Questions For You
                                            </h4>
                                        </span>
                                        <h4 v-else class="square-inline text-start mr-auto">  No New Fan Questions! </h4>
                                    </div>
                                    <!-- body -->
                                    <div v-if="unansweredQuestions.length != 0">
                                        <div style="display: flex; align-items: center; justify-content: center;">
                                            <router-link :to="{ path: '/Producers/ProducersQA/' + userID }">
                                                <button class="btn secondary-btn-border btn-sm py-2 px-3"  style="font-weight: bold;"> Respond to Q&A </button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- activity -->
                            <div class="col-12">
                                <div class="square primary-square-green-outline rounded p-3 mb-3">  <!--tzh changed to green outline -->
                                    <!-- header text -->
                                    <div class="square-inline">
                                        <h4 class="square-inline text-start mr-auto"> Activity on Your Listings </h4>
                                    </div>
                                    <!-- body -->
                                    <div>
                                        <div style="display: flex; align-items: center; justify-content: center;">
                                            <router-link :to="{ path: '/profile/producer/' + userID }">
                                                <button class="btn secondary-btn-border btn-sm py-2 px-3" style="font-weight: bold;"> View Dashboard </button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- [venue] fan questions / check ins -->
                        <div v-else-if="userType == 'venue'" class="row">
                            <!-- fan questions -->
                            <div class="col-12">
                                <div class="square primary-square-green-outline rounded p-3 mb-3">  <!--tzh changed to green outline -->
                                    <!-- header text -->
                                    <div class="square-inline">
                                        <span v-if="unansweredQuestions.length != 0" class="square-inline text-start mr-auto">
                                            <h4>
                                                <span class="title-card-text"> {{ unansweredQuestions.length }} </span>  Pending Fan Questions For You
                                            </h4>
                                        </span>
                                        <h4 v-else class="square-inline text-start mr-auto">  No New Fan Questions! </h4>
                                    </div>
                                    <!-- body -->
                                    <div v-if="unansweredQuestions.length != 0">
                                        <div style="display: flex; align-items: center; justify-content: center;">
                                            <router-link :to="{ path: '/Venues/VenuesQA/' + userID }">
                                                <button class="btn secondary-btn-border btn-sm py-2 px-3" style="font-weight: bold;"> Respond to Q&A </button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- check ins at your venue -->
                            <div class="col-12">
                                <div class="square primary-square-green-outline rounded p-3 mb-3">  <!--tzh changed to green outline -->
                                    <!-- header text -->
                                    <div class="square-inline">
                                        <h4 class="square-inline text-start mr-auto"> Activity on Your Listings </h4>
                                    </div>
                                    <!-- body -->
                                    <div>
                                        <div style="display: flex; align-items: center; justify-content: center;">
                                            <router-link :to="{ path: '/profile/venue/' + userID }">
                                                <button class="btn secondary-btn-border btn-sm py-2 px-3" style="font-weight: bold;"> View Dashboard </button>
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
                <!-- discover, following & filter by drink type -->
                <div class="col-lg-9 col-md-8 col-12">
                    <div class="container">
                        <div class="row ps-lg-4 pe-lg-4 mobile-ps-3 mobile-pe-3">
                            <!-- discover  tzh changed col-12 to col-4-->
                            <div class="col-xl-3 col-lg-4 col-4 mb-3 mobile-pe-0 mobile-ps-0">
                                <div class="d-grid gap-2  mx-1">
                                    <button class="btn btn-sm mobile-ps-0 text-center" 
                                        :class="{ 'primary-btn-green mobile-convert-to-toggle-button mobile-pt-2 mobile-pb-0 mobile-pe-0': discovery, 'primary-btn-green-outline mobile-convert-to-toggle-button mobile-pt-2 mobile-pb-0': !discovery }"
                                        v-on:click="changeDiscoveryStatus()"> <!--tzh added -green and green-outline, changed mt-1 to mb-0_5 mt-0_5 -->
                                        <p class="mb-0_5 mt-0_5 discover-and-following mobile-mb-0"> Results for {{ $route.query.logo }} </p>
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- listings  TZH removed class scrollable-listings--->
                        <div class="row">

                            <!-- [if] discovery mode-->
                            <div v-if="discovery == true || following == false" class="mobile-ps-0 mobile-pe-0">
                                <!-- Display error message when no results for filter-->

                                 <!-- Displays Message if there are no listing available  -->
                                <h5 v-if="listings == '' || (selectedDrinkType!='' && filteredListings=='')" style="display: inline-block;" class="pt-5"> There is no listing available for the selected filter </h5>
                                <!-- v-loop for each listing -->
                                <div class="container text-start mobile-ps-0 mobile-pe-0">
                                    <!-- Displays listings from all general listings or from filtered listings from drinkCategory/drinkType depending if filter is selected-->
                                    <!-- <div v-for="listing in filteredListings" v-bind:key="listing.id" class="p-3 mobile-pt-0"> -->
                                    <div v-for="listing in (selectedDrinkType == '' ? listings : filteredListings)" v-bind:key="listing.id" class="p-3 mobile-pt-0">

                                        <div class="row">
                                            <!-- image -->
                                            <div class="col-5 "> <!-- tzh changed col-xl-5 col-12 to col-5 -->
                                                <div class="image-container mb-3 homepage" >
                                                    <img v-if="listing['photo']" :src="listing['photo']" class="img-border object-fit-contain homepage">
                                                    <img v-else src="../../Images/Drinks/Placeholder.png"  class="img-border object-fit-contain homepage">
                                                    <div class="mobile-view-hide">
                                                    <BookmarkIcon 
                                                        v-if="user" 
                                                        :user="user" 
                                                        :listing="listing" 
                                                        :overlay="true"
                                                        size="30"
                                                        @icon-clicked="handleIconClick" />
                                                    </div>    
                                                </div>
                                            </div>
                                            <!-- details -->
                                            <div class="col-7 mobile-p-0"> <!-- tzh changed col-xl-5 col-12 ps-lg-0 to col-7 mobile-p-0 -->
                                                <!-- expression name -->
                                                <div class="row pt-1">
                                                    <router-link :to="{ path: '/listing/view/' +listing.id }" class="primary-clickable-text mobile-col-12"> <!--tzh changed mobile-col-10 to mobile-col-12 -->
                                                        <h4 class="mobile-mb-0 mobile-view-hide"> <b> {{ listing["listingName"] }} </b> </h4> <!-- tzh added mobile-mb-0-->
                                                        <h6 class="mobile-mb-0 mobile-view-show"> <b> {{ listing["listingName"] }} </b> </h6> <!-- tzh added mobile-mb-0-->
                                                    </router-link>
                                                    <!--<div class="mobile-col-2 mobile-view-show"> 
                                                        <BookmarkIcon 
                                                        v-if="user" 
                                                        :user="user" 
                                                        :listing="listing" 
                                                        :overlay="true"
                                                        size="30"
                                                        @icon-clicked="handleIconClick" />
                                                    </div>-->
                                                </div>
                                                <!-- producer -->
                                                <div class="row mobile-view-hide"> <!-- tzh added mobile-view-hide -->
                                                    <router-link :to="{ path: '/profile/producer/' + listing.producerID }" class="primary-clickable-text">
                                                        <h5 class="mobile-rating-smaller-text"> <b> {{ getProducerName(listing) }} </b> </h5>
                                                    </router-link>
                                                </div>
                                                <!-- review tzh shortened description if above 270 characters  -->
                                                <div class="row pt-3">
                                                    <div class="mobile-col-11 mobile-pe-0"> <!-- tzh changed mobile-col-9 to mobile-col-11 -->
                                                    <router-link :to="{ path: '/listing/view/' +listing.id }" class="default-clickable-text fst-italic scrollable-user-bottle-listings-description-box">
                                                        <span class="mobile-view-hide"> <!-- tzh added this section below -->
                                                            <div v-if="listing.officialDesc?.length > 300">  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"].slice(0, 300) + (listing["officialDesc"].length > 300 ? '...' : '') }} </p>
                                                            </div>
                                                            <div v-else>  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"] }}. </p>
                                                            </div>
                                                        </span>
                                                        <span class="mobile-view-show"> <!-- tzh added this section below -->
                                                            <div v-if="listing.officialDesc?.length > 80">  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"].slice(0, 300) + (listing["officialDesc"].length > 300 ? '...' : '') }} </p>
                                                            </div>
                                                            <div v-else>  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"] }}. </p>
                                                            </div>
                                                        </span>
                                                    </router-link>
                                                    </div>
                                                    <!-- tzh commented out rating -->
                                                   <!--<div class="mobile-col-3 mobile-view-show mobile-ps-0">
                                                        <h2 class="rating-text text-end d-flex align-items-center">
                                                            {{ getRatings(listing) }} ★
                                                            <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-star-fill ms-1" viewBox="0 0 16 16">
                                                                <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                                                            </svg>
                                                        </h2>   
                                                    </div>-->    
                                                </div>
                                                <!-- rating -->
                                                <div class="row pt-4 mobile-pt-0"> <!--tzh removed mobile-view-hide and added mobile-pt-0 -->
                                                    <div class="col-6 d-flex align-items-center">
                                                        <h1 class="rating-text text-end d-flex align-items-center mobile-view-hide">
                                                            {{ getRatings(listing) }} ★
                                                            <!--<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-star-fill ms-1" viewBox="0 0 16 16">
                                                                <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                                                            </svg>-->
                                                        </h1>
                                                        <h5 class="rating-text text-end d-flex align-items-center mobile-view-show">
                                                            {{ getRatings(listing) }} ★
                                                            <!--<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-star-fill ms-1" viewBox="0 0 16 16">
                                                                <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                                                            </svg>-->
                                                        </h5>
                                                    </div>
                                                    <div class="col-6 text-end mobile-view-hide"> <!--tzh added mobile-view-hide -->
                                                        <div class="d-grid gap-5">
                                                            <router-link :to="{ path: '/listing/view/' +listing.id }" class="primary-clickable-text">
                                                                <a class="btn secondary-btn btn-md" style="font-weight: bold;"> Read More </a>
                                                            </router-link>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div> <!-- end of listings -->

                            <!-- [else] following clicked -->
                            <div v-else-if="following || discovery == false" class="mobile-ps-0 mobile-pe-0">


                                <!-- latest reviews from users the current user is following -->
                                <h3 class="text-body-secondary text-start pt-3"> 
                                    <b> Latest Reviews from Followed Users</b>
                                </h3>
                                <!-- v-loop for each review -->
                                <div class="container text-start">
                                    <h5 v-if="latestReviews.length == 0" style="display: inline-block;"> There is no listing available for the selected filter </h5>
                                    <div v-else v-for="review in latestReviews" v-bind:key="review.id" class="p-3 mobile-pt-0">

                                        <!-- For latest reviews -->
                                        <div class="row gap-3">

                                            <!-- row 1: For followed user info and reviewTarget name-->
                                            <div class="row my-auto">
                                                <!-- Column 1: Followed user photo-->
                                                <div class="col-2 d-flex justify-content-center">
                                                    <img :src="(review['userInfo']['photo'] || defaultProfilePhoto)" class="w-50 h-100 rounded-circle">
                                                </div>

                                                <!-- Column 2: Followed user displayName and reviewTarget listingName-->
                                                <div class="col-10 d-flex align-items-center gap-2">
                                                    <router-link :to="{ path: '/profile/user/' + review.userID }" class="primary-clickable-text">
                                                        <h5> <b> @{{ review['userInfo']['displayName'] }} </b> </h5>
                                                    </router-link>
                                                    <h5>just drank and rated </h5>
                                                    <router-link :to="{ path: '/listing/view/' +review.reviewTarget.id }" class="primary-clickable-text">
                                                        <h5> <b> {{ review['reviewTarget']['listingName'] }} </b> </h5>
                                                    </router-link>
                                                </div>

                                            </div>

                                            <!-- row 2: For reviewTarget photo, review description, rating and "View drink listing" button-->
                                            <div class="row">
                                                <!--Column 1: listing image-->
                                                <!-- image -->
                                                <div class="col-md-5 col-12">
                                                    <div class="image-container mb-3 homepage" >
                                                        <img v-if="review['reviewTarget']['photo']" :src="review['photo']" class="img-border homepage">
                                                        <img v-else src="../../Images/Drinks/Placeholder.png" class="img-border homepage">
                                                    </div>
                                                </div>

                                                <!-- Column 2: rating description, rating and "View drink listing" button-->                                                
                                                <div class="col-md-7 col-12 d-flex flex-column justify-content-between">

                                                    <!-- Row 1 in column 2: Rating description-->
                                                    <div class="row">
                                                        <h5> "{{ review["reviewDesc"] }}" </h5>
                                                    </div>

                                                    <!-- Row 2 in column 2: Rating and "View drink listing" button-->
                                                    <div class="row">
                                                        <!-- Rating -->
                                                        <div class="col-6 d-flex align-items-center">
                                                            <h1 class="rating-text text-end d-flex align-items-center">
                                                                {{ review["rating"] }}
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-star-fill ms-1" viewBox="0 0 16 16">
                                                                    <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                                                                </svg>
                                                            </h1>
                                                        </div>

                                                        <!-- "View drink listing" button -->
                                                        <div class="col-6">
                                                            <div class="d-grid gap-5">
                                                                <router-link :to="{ path: '/listing/view/' +review.reviewTarget.id }" class="primary-clickable-text">
                                                                    <a class="btn secondary-btn btn-lg" style="font-weight: bold;"> View Drink Listing </a>
                                                                </router-link>
                                                            </div>
                                                        </div>  
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>


                                <!-- recently added  -->
                                <h3 class="text-body-secondary text-start pt-3"> 
                                    <b> Recently Added </b> 
                                </h3>
                                <!-- v-loop for each listing -->
                                <div class="container text-start">
                                    <h5 v-if="recentlyAdded==''" style="display: inline-block;"> There is no listing available for the selected filter </h5>
                                    <h5 v-if="recentlyAdded == '' || (selectedDrinkType!='' && filteredRecentlyAdded=='')" style="display: inline-block;"> There is no listing available for the selected filter </h5>
                                    <!-- <div v-for="listing in recentlyAdded" v-bind:key="listing.id" class="p-3 mobile-pt-0"> -->
                                    <div v-for="listing in (selectedDrinkType == '' ? recentlyAdded : filteredRecentlyAdded)" v-bind:key="listing.id" class="p-3 mobile-pt-0">
                                        <!-- For latest reviews -->
                                        
                                        <!-- For listings -->
                                        <div class="row">
                                            <!-- image -->
                                            <div class="col-5"> <!-- tzh changed col-xl-5 col-12 to col-5 -->
                                                <div class="image-container mb-3 homepage" >
                                                    <img v-if="listing['photo']" :src="listing['photo']"  class="img-border homepage">
                                                    <img v-else src="../../Images/Drinks/Placeholder.png" class="img-border homepage">
                                                    <div class="mobile-view-hide">
                                                    <BookmarkIcon 
                                                        v-if="user" 
                                                        :user="user" 
                                                        :listing="listing" 
                                                        :overlay="true"
                                                        size="30"
                                                        @icon-clicked="handleIconClick" />
                                                    </div>    
                                                </div>
                                            </div>
                                            <!-- details -->
                                            <div class="col-7 mobile-p-0"> <!-- tzh changed col-xl-5 col-12 ps-lg-0 to col-7 mobile-p-0 -->
                                                <!-- expression name -->
                                                <div class="row pt-1">
                                                    <router-link :to="{ path: '/listing/view/' +listing.id }" class="primary-clickable-text mobile-col-12"> <!--tzh changed mobile-col-10 to mobile-col-12 -->
                                                        <h4 class="mobile-mb-0 mobile-view-hide"> <b> {{ listing["listingName"] }} </b> </h4> <!-- tzh added mobile-mb-0-->
                                                        <h6 class="mobile-mb-0 mobile-view-show"> <b> {{ listing["listingName"] }} </b> </h6> <!-- tzh added mobile-mb-0-->
                                                    </router-link>
                                                    <!--<div class="mobile-col-2 mobile-view-show">
                                                    <BookmarkIcon 
                                                        v-if="user" 
                                                        :user="user" 
                                                        :listing="listing" 
                                                        :overlay="true"
                                                        size="30"
                                                        @icon-clicked="handleIconClick" />
                                                    </div>-->  
                                                </div>
                                                <!-- producer -->
                                                <div class="row mobile-view-hide">  <!-- tzh added mobile-view-hide -->
                                                    <router-link :to="{ path: '/profile/producer/' + listing.producerID }" class="primary-clickable-text">
                                                        <h5 class="mobile-rating-smaller-text"> <b> {{ getProducerName(listing) }} </b> </h5>
                                                    </router-link>
                                                </div>
                                                <!-- review -->
                                                <div class="row pt-3">
                                                    <!-- tzh transplanted code below from another section-->
                                                    <div class="mobile-col-11 mobile-pe-0"> <!-- tzh changed mobile-col-9 to mobile-col-11 -->
                                                    <router-link :to="{ path: '/listing/view/' +listing.id }" class="default-clickable-text fst-italic scrollable-user-bottle-listings-description-box">
                                                        <span class="mobile-view-hide"> <!-- tzh added this section below -->
                                                            <div v-if="listing.officialDesc?.length > 300">  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"].slice(0, 300) + (listing["officialDesc"].length > 300 ? '...' : '') }} </p>
                                                            </div>
                                                            <div v-else>  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"] }}. </p>
                                                            </div>
                                                        </span>
                                                        <span class="mobile-view-show"> <!-- tzh added this section below -->
                                                            <div v-if="listing.officialDesc?.length > 80">  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"].slice(0, 300) + (listing["officialDesc"].length > 300 ? '...' : '') }} </p>
                                                            </div>
                                                            <div v-else>  
                                                                <p class="homepage-bottle-listing-description"> {{ listing["officialDesc"] }}. </p>
                                                            </div>
                                                        </span>
                                                    </router-link>
                                                    </div>
                                                    <!-- tzh commented out to make way for code above <router-link :to="{ path: '/listing/view/' +listing.id }" class="default-clickable-text fst-italic scrollable">
                                                        <h5> {{ listing["officialDesc"] }}. </h5>
                                                    </router-link>-->
                                                </div>
                                                <!-- rating -->
                                                <div class="row pt-4 mobile-pt-0">  <!--tzh added mobile-pt-0 -->
                                                    <div class="col-6 d-flex align-items-center">
                                                        <h1 class="rating-text text-end d-flex align-items-center mobile-view-hide">
                                                            {{ getRatings(listing) }} ★
                                                            <!--<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-star-fill ms-1" viewBox="0 0 16 16">
                                                                <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                                                            </svg>-->
                                                        </h1>
                                                        <h5 class="rating-text text-end d-flex align-items-center mobile-view-show">
                                                            {{ getRatings(listing) }} ★
                                                            <!--<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-star-fill ms-1" viewBox="0 0 16 16">
                                                                <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                                                            </svg>-->
                                                        </h5>
                                                    </div>
                                                    <div class="col-6 mobile-view-hide"> <!--tzh added mobile-view-hide -->
                                                        <div class="d-grid gap-5">
                                                            <router-link :to="{ path: '/listing/view/' +listing.id }" class="primary-clickable-text">
                                                                <a class="btn secondary-btn btn-md"> Read what the crowd thinks </a>
                                                            </router-link>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="d-grid justify-content-center align-content-center">
                                <button v-if="moreListings" class="btn secondary-btn btn-md" style="font-weight: bold;" @click = "retrieveListings"> Click to load more! </button>
                            </div>

                        </div> <!-- end of scrollable section -->

                    </div> <!-- end of container -->
                </div> <!--  end of discover, following & filter by drink type -->
            </div> <!-- end of row -->
        </div>
    </div>

    <!-- [else] with search inputs -->
    <div>
        <BookmarkModal 
            v-if="user"
            :user="user" 
            :listings="listings" 
            :listingID="bookmarkListingID" />
    </div>

</template>

<!-- ---------------------------------------------------------------------------------------------------------------------------------------------------------- -->

<!-- JavaScript -->
<script>
console.log("API URL:", process.env.VUE_APP_API_URL);
    import NavBar from '@/components/NavBar.vue';
    import BookmarkIcon from '@/components/BookmarkIcon.vue';
    import BookmarkModal from '@/components/BookmarkModal.vue';

    export default {
        components: {
            NavBar,
            BookmarkIcon, 
            BookmarkModal
        },

        data() {
            return {
                dataLoaded: false,
                // data from database
                // countries: [],
                listings: [],
                producers: [],
                reviews: [],
                users: [],
                venues: [],
                venuesAPI: [],
                drinkTypes: [],
                requestListings: [],
                requestEdits: [],
                requestDupes: [],
                modRequests: [],

                // for user account credentials
                userID: "",
                userType: "",
                types: [],
                username: "",
                displayName: "",
                isAdmin: "",
                isModerator: "",
                drinkShelf: [],

                // for producer listing information
                totalRequests: 0,
                unansweredQuestions: [],

                // search
                search: false,
                searchInput: '',
                searchTerm: '',
                searchResults: [],
                filteredListings: [],
                searchHistory: [],

                // for filter by drink categories
                selectedDrinkType:"",
                selectedTypeCategory:[],
                selectedCategory:"",
                filterSearchResult: [],
                isFilterType:false,
                moreListings:true,

                // for sort function
                sortSelection: {
                    category: ''
                },
                sortCategoryList: [
                    'Alphabetical (A - Z)',
                    'Alphabetical (Z - A)',
                    'Date (Newest - Oldest)',
                    'Date (Oldest - Newest)',
                    'Ratings (Highest - Lowest)',
                    'Ratings (Lowest - Highest)',
                ],
                sortedListings: [],

                // customization for drinkLists buttons
                // [TODO] get drink list of user, for now is hardcoded
                drinkList:  {
                                "haveTried": ["Harmony Collection Inspired by Intense Arabica"],
                                "wantToTry": ["Catnip Gin No. 2", "Five Farms Irish Cream Liqueur"]
                            },
                haveTried: false,
                wantToTry: false,

                // for discovery - tzh changed 'false' to 'true'
                discovery: true,
                allReviews: {},
                mostReviews: [],

                // for following
                following: false,
                userFollowing: [], // list of users that the current user is following
                followedProducers: [],
                followedVenues: [],
                allProducerDrinks: [],
                allVenueDrinks: [],
                recentlyAdded: [],
                filteredRecentlyAdded:[],
                questionsUpdates: [],
                followCount:0,

                // for bookmark
                user: null,
                userBookmarks: [],

                // for latest reviews by users that the current user is following
                latestReviews: [],
                
                // for bookmark component
                bookmarkListingID: {},

                defaultProfilePhoto: "https://drinkximages.s3.us-east-1.amazonaws.com/images/2d4d94bc-313e-4621-9a15-4bfbf77958de.jpg",
            };
        },
        mounted() {
            // Load local storage variables
            const accID = localStorage.getItem("88B_accID");
            if(accID !== null){
                this.userID = localStorage.getItem('88B_accID')
            }
            let userType = localStorage.getItem('88B_accType')
            if(userType !=null){
                this.userType = userType
            }
            this.loadData();
        },
        methods: {
            // load data from database, listings
            async loadData() {
                try {
                    const logo = this.$route.query.logo; // Get the logo from URL parameters

                    if (!logo) {
                        console.warn("No logo parameter found in query.");
                        return;
                    }

                    const response = await this.$axios.post(
                        `${process.env.VUE_APP_API_URL}/getData/getListingsByLogo`,
                        { logo: logo },  // Pass logo as a request body
                        { headers: { "Content-Type": "application/json" } }
                    );

                    if (response.status === 200 && response.data.length > 0) {
                        this.listings = response.data; // Store API results
                        this.filteredListings = this.listings;
                        this.dataLoaded = true;
                    } else {
                        console.warn("No listings found for logo:", logo);
                        this.listings = [];
                        this.filteredListings = [];
                        this.dataLoaded = false;
                    }
                } catch (error) {
                    console.error("Error fetching listings:", error);
                    this.listings = [];
                    this.filteredListings = [];
                    this.dataLoaded = false;
                }
                // producers
                // _id, producerName, producerDesc, originCountry, statusOB, mainDrinks
                // TODO: make retrieved producers only for listings that are retrieved initially
                    try {
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getProducers`);
                        this.producers = response.data;
                    } 
                    catch (error) {
                        console.error(error);
                        this.dataLoaded = null;
                    }
                // reviews
                // _id, userID, reviewTarget, date, rating, reviewDesc, taggedUsers, reviewTitle, reviewType, flavorTag, photo
                // TODO: make retrieved reviews only for the listings that are retrieved initially
                    try {
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getReviews`);
                        this.reviews = response.data;
                        this.getAllReviews()
                        this.getMostReviews()
                    }
                    catch (error) {
                        console.error(error);
                        this.dataLoaded = null;
                    }
                // venues
                // _id, venueName, venueDesc, originCountry, address, openingHours
                try {
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getVenues`);
                        this.venues = response.data;
                    } 
                    catch (error) {
                        console.error(error);
                        this.dataLoaded = null;
                    }
                // users
                // _id, username, displayName, choiceDrinks, drinkLists, modType, photo
                try {
                    const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getUser/${this.userID}`);
                    this.user = response.data;
                    if (this.user) {
                        // Get the list of users that the current user is following

                        this.userBookmarks = this.user.drinkLists;
                        this.getFollowedProducers()
                        this.getFollowedVenues()
                        this.getListingsByProducer()
                        this.getListingsByVenue()
                        this.getRecentlyAdded()
                        this.getQuestionsUpdates();
                        
                        if (this.user.followLists.users.length > 0) {
                            this.userFollowing = this.user.followLists.users;
                            // Get the latest reviews from users that the current user is following
                            this.getUsersLatestReviews()
                        }
                        // check if user is an admin
                        if (this.user.isAdmin) {
                            this.isAdmin = true
                        }
                        // if user is not admin, check if user is a moderator
                        if (this.user.modType.length > 0) {
                            this.isModerator = true
                        }
                    }
                } 
                catch (error) {
                    console.error(error);
                    // this.dataLoaded = null;
                }
                // venuesAPI
                // _id, venueName, venueDesc, originCountry
                // try {
                //         const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getVenuesAPI`);
                //         this.venuesAPI = response.data;
                //     } 
                //     catch (error) {
                //         console.error(error);
                //     }
                // drinkTypes
                // _id, drinkType, typeCategory
                    try {
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getDrinkTypes`);
                        this.drinkTypes = response.data;
                        this.drinkTypes.sort((a,b)=>{
                            return a.drinkType.localeCompare(b.drinkType)
                        })
                    } 
                    catch (error) {
                        console.error(error);
                        this.dataLoaded = null;
                    }
                // requestListings
                // _id, listingName, producerNew, producerID, bottler, originCountry, drinkType, typeCategory, age, abv, reviewLink, sourceLink, brandRelation, reviewStatus, userID, photo
                    try {
                            const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getRequestListings`);
                            this.requestListings = response.data;
                            // Filter requests based on user role
                            if (this.userType == 'producer') {
                                this.requestListings = response.data.filter((request) => {
                                    return request["reviewStatus"] == false && request["producerID"] == this.userID;
                                })
                            }
                            else if (this.userType == 'user') {
                                if (this.isAdmin) {
                                    this.requestListings = response.data.filter((request) => {
                                        return request["reviewStatus"] == false;
                                    })
                                } else {
                                    this.requestListings = response.data.filter((request) => {
                                        return request["reviewStatus"] == false && (request["userID"] == this.userID || this.types.includes(request["drinkType"]));
                                    })
                                }
                            }
                        } 
                    catch (error) {
                        console.error(error);
                        this.dataLoaded = null;
                    }
                // requestEdits
                // _id, duplicateLink, editDesc, sourceLink, brandRelation, listingID, userID, reviewStatus
                    try {
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getRequestEdits`);
                        let unreviewedRequests = response.data.filter((request) => {
                            return request["reviewStatus"] == false;
                        });

                        // Obtain listing data for each request
                        for (let request of unreviewedRequests) {
                            let targetListing = this.listings.find((listing) => {
                                return listing["id"] == request["listingID"];
                            });
                            if (targetListing == undefined) {
                                continue;
                            }

                            request['photo'] = targetListing['photo'];
                            request['listingName'] = targetListing['listingName'];
                            request['producerID'] = targetListing['producerID'];

                            if (request['duplicateLink']) {
                                this.requestDupes.push(request);
                            } else {
                                this.requestEdits.push(request);
                            }
                        }

                        // Filter requests based on user role
                        if (this.userType == 'producer') {
                            this.requestEdits = this.requestEdits.filter((request) => {
                                return request["producerID"] == this.userID;
                            })
                            this.requestDupes = this.requestDupes.filter((request) => {
                                return request["producerID"] == this.userID;
                            })
                        }
                        else if (this.userType == 'user' && !this.isAdmin) {
                            this.requestEdits = this.requestEdits.filter((request) => {
                                return request["userID"] == this.userID || this.types.includes(request["drinkType"]);
                            })
                            this.requestDupes = this.requestDupes.filter((request) => {
                                return request["userID"] == this.userID || this.types.includes(request["drinkType"]);
                            })
                        }
                    } 
                    catch (error) {
                        console.error(error);
                        this.dataLoaded = null;
                    }
                // modRequests
                // _id, userID, drinkType, modDesc
                    // try {
                    //         const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getModRequests`);
                    //         this.modRequests = response.data;
                    //     } 
                    // catch (error) {
                    //     console.error(error);
                    // }

                this.getUsername()
                // listing requests
                this.totalRequests = this.requestListings.length + this.requestEdits.length + this.requestDupes.length;

                // set dataLoaded to true
                if (this.dataLoaded != null) {
                    this.dataLoaded = true;
                }
            },

            // get username of user accessing page
            getUsername() {
                let producer = this.producers.find(producer => producer.id == parseInt(this.userID))
                let venue = this.venues.find(venue => venue.id == parseInt(this.userID))
                if (this.user && this.userType == 'user') {
                    this.username = this.user.username
                    this.displayName = this.user.displayName
                    // drink shelf
                    let allDrinkShelf = Object.values(this.user.drinkLists).flatMap(obj => obj.listItems);
                    allDrinkShelf.sort((a, b) => {
                        return new Date(b[0]) - new Date(a[0]);
                    })
                    let allDrinks = []
                    for (const item of allDrinkShelf) {
                        const listing = this.listings.find(listing => listing.id === parseInt(item));
                        if (listing) {
                            allDrinks.push(listing);
                        }
                    }
                    this.drinkShelf = [...new Set(allDrinks)];
                }
                else if (producer && this.userType == 'producer') {
                    this.username = producer.producerName
                    // Q&A
                    let answeredQuestions = producer["questionsAnswers"];
                    if (answeredQuestions.length > 0) {
                        for (let qa in answeredQuestions) {
                            let answer = answeredQuestions[qa]["answer"];
                            if (answer == "") {
                                this.unansweredQuestions.push(answeredQuestions[qa]);
                            }
                        }
                    }
                }
                else if (venue) {
                    this.username = venue.venueName

                    // Q&A
                    let answeredQuestions = venue["questionsAnswers"];
                    if (answeredQuestions.length > 0) {
                        for (let qa in answeredQuestions) {
                            let answer = answeredQuestions[qa]["answer"];
                            if (answer == "") {
                                this.unansweredQuestions.push(answeredQuestions[qa]);
                            }
                        }
                    }
                }
            },

            // Helper function for onkeyup search to reset filter
            // helperSearch(){
            //     this.searchListings()
            //     this.isFilterType = false
            //     this.selectedDrinkType = ''
            // },

            // for search button
            // searchListings() {
            //     // flag to check if there are search inputs
            //     const searchInput = this.searchInput.toLowerCase();
            //     this.searchTerm = this.searchInput;

            //     // if there is something searched
            //     this.search = true;
            //     const searchResults = this.listings.filter((listing) => {
            //         const expressionName = listing["listingName"].toLowerCase();
            //         const producer = this.getProducerName(listing).toLowerCase(); //error here if return null, meaning drink doesnt belong to any producer
            //         return expressionName.includes(searchInput) || producer.includes(searchInput);
            //     });

            //     // add search results to search history
            //     this.searchHistory.push([searchInput, searchResults]);

            //     // if nothing found
            //     if (searchResults.length == 0) {
            //         this.filteredListings = [];
            //     } 
            //     else {
            //         this.filteredListings = searchResults;
            //     }

            //     // if there is nothing searched
            //     if (this.searchInput == '') {
            //         this.resetListings();
            //     }
            // },

            // for viewing previous listings (show previous search results)
            // previousListing() {
            //     // more than 1 search result history
            //     if (this.searchHistory.length > 1) {
            //         // remove current search result
            //         this.searchHistory.pop();
            //         // get previous search result
            //         const previousSearch = this.searchHistory[this.searchHistory.length - 1];
            //         this.searchInput = previousSearch[0];
            //         this.searchTerm = this.searchInput;
            //         this.filteredListings = previousSearch[1];
            //     }
            //     // only 1 search result history
            //     else {
            //         this.resetListings();
            //     }
            // },

            // for resetting listings (show full listings)
            resetListings() {
                this.searchInput = '';
                this.search = false;
                this.filteredListings = this.listings;
                this.searchHistory = [];
                this.moreListings=true
            },

            // get producerName for a listing based on listing
            getProducerName(listing) {
                const producer = this.producers.find((producer) => {
                    return producer["id"] == listing["producerID"];
                });
                // ensures that producer is found before accessing "producerName"
                if (producer) {
                    const producerName = producer["producerName"];
                    return producerName;
                }
                else {
                    return null;
                }
            },

            // get reviews for a listing
            getReviews(listing) {
                // list of all reviews of the particular drink
                const reviews = this.reviews.filter((review) => {
                    return review["reviewTarget"] == listing["listingName"];
                });
                // choose random review from the list
                const randomReview = reviews[Math.floor(Math.random() * reviews.length)];
                // check if a review is found before accessing "Review Desc"
                const reviewDesc = randomReview ? randomReview["reviewDesc"] : null;
                return reviewDesc;
            },

            // get ratings for a listing
            getRatings(listing) {
                const ratings = this.reviews.filter((rating) => {
                    return rating["reviewTarget"] == listing["id"];
                });
                // if there are no ratings
                if (ratings.length == 0) {
                    return "-";
                }
                // else there are ratings
                const averageRating = ratings.reduce((total, rating) => {
                    return total + rating["rating"];
                }, 0) / ratings.length;
                return averageRating.toFixed(1); //tzh changed .toFixed(2) to .toFixed(1)
            },

            // get ratings for a listing --> return 0 if no ratings
            getAllRatings(listing) {
                const ratings = this.reviews.filter((rating) => {
                    return rating["reviewTarget"] == listing["id"];
                });
                // if there are no ratings
                if (ratings.length == 0) {
                    return 0;
                }
                // else there are ratings
                const averageRating = ratings.reduce((total, rating) => {
                    return total + rating["rating"];
                }, 0) / ratings.length;
                // round to 1 decimal place
                const roundedRating = Math.round(averageRating * 10) / 10;
                return roundedRating;
            },

            // Handle select of drink type filter option like sake, gin, whiskey
            selectDrinkType(drinkType) {

                // reset most reviews and recently added arrays so that can repeatedly filter
                this.getMostReviews()
                this.moreListings=true
                // Determine selected drink type, and corresponding drink categories
                this.selectedCategory = null;
                this.selectedDrinkType = drinkType;
                for(let drinks of this.drinkTypes){
                    if(drinks['drinkType'] == drinkType['drinkType']){
                        this.selectedTypeCategory = drinks['typeCategory']
                    }
                }

                // Determine the drinkType searched, might not be neccessary
                const drinkTypeSearch = this.selectedDrinkType['drinkType']?.toLowerCase();


                // Search listings for when input is in the searchbar
                // if(this.search){
                //     this.searchListings()
                //     const searchResults = this.filteredListings.filter((listing) => {
                //         const drinkTypeListing = listing["drinkType"].toLowerCase();
                //         return drinkTypeListing.includes(drinkTypeSearch);
                //     });
                //     this.filterSearchResult=searchResults
                //     // to set filter message together with search terms when searched listings
                //     this.isFilterType = true
                // }

                // Filter listings for when discovery mode
                if(this.discovery){

                    const searchResults = this.mostReviews.filter((listing) => {
                        const drinkTypeListing = listing["drinkType"].toLowerCase();
                        return drinkTypeListing.includes(drinkTypeSearch);
                    });
                    // if nothing found
                    if(searchResults.length==0 || searchResults==null){
                        this.mostReviews = []
                        this.filteredListings = []
                        this.retrieveListings()
                    }
                    else{
                        this.mostReviews=searchResults
                        this.filteredListings = searchResults
                        if(this.filteredListings.length<30){
                            this.retrieveListings();
                        }
                    }

                }

                // Filter listings for when following mode
                else if(this.following){
                    const searchResults = this.recentlyAdded.filter((listing) => {
                        const drinkTypeListing = listing["drinkType"].toLowerCase();
                        return drinkTypeListing.includes(drinkTypeSearch);
                    });

                    // if nothing found
                    if(searchResults == null){
                        this.filteredRecentlyAdded = []
                    }
                    else{
                        this.filteredRecentlyAdded=searchResults
                    }
                }
            },

            // Function to sort results based on selected category
            sortResults() {
                let category = this.sortSelection.category;

                // ------ SORT LISTINGS --------
                // #1: Alphabetical (A - Z)
                if (category == 'Alphabetical (A - Z)') {
                    this.filteredListings.sort((a, b) => {
                        return a.listingName.localeCompare(b.listingName);
                    });
                }
                // #2: Alphabetical (Z - A)
                else if (category == 'Alphabetical (Z - A)') {
                    this.filteredListings.sort((a, b) => {
                        return b.listingName.localeCompare(a.listingName);
                    });
                }
                // #3: Date (Newest - Oldest)
                else if (category == 'Date (Newest - Oldest)') {
                    this.filteredListings.sort((a, b) => {
                        return new Date(b.addedDate) - new Date(a.addedDate);
                    });
                }
                // [DEFAULT] #4: Date (Oldest - Newest)
                else if (category == '' || category == 'Date (Oldest - Newest)') {
                    this.filteredListings.sort((a, b) => {
                        return new Date(a.addedDate) - new Date(b.addedDate);
                    });
                }
                // #5: Ratings (Highest - Lowest)
                else if (category == 'Ratings (Highest - Lowest)') {
                    this.filteredListings.sort((a, b) => {
                        return this.getAllRatings(b) - this.getAllRatings(a);
                    });
                }
                // #6: Ratings (Lowest - Highest)
                else if (category == 'Ratings (Lowest - Highest)') {
                    this.filteredListings.sort((a, b) => {
                        return this.getAllRatings(a) - this.getAllRatings(b);
                    });
                }
            },

            // Sort Support Function (Category)
            sortByCategory(category) {
                // Check if the selected filter is the same as the current filter
                if (this.sortSelection.category == category) {
                    return;
                }
                else {
                    this.sortSelection.category = category
                    this.sortResults();
                }
            },

            //Select drink category like Blended for whiskey 
            selectDrinkCategory(drinkCategory) {
                this.selectDrinkType(this.selectedDrinkType)
                this.selectedCategory = drinkCategory;
                const drinkCategorySearch = this.selectedCategory.toLowerCase();

                if(this.discovery){
                    const searchResults = this.mostReviews.filter((listing) => {
                        const drinkCategory = listing["typeCategory"].toLowerCase();
                        return drinkCategory.includes(drinkCategorySearch);
                    });
                    if (searchResults.length ==0) {
                        this.errorFound = true;
                        this.errorMessage = 'No results found, please try again.';
                        this.mostReviews = [];
                        this.filteredListings = [];
                        this.retrieveListings();
                    } 
                    else {
                        this.errorFound = false;
                        this.errorMessage = '';
                        this.mostReviews = searchResults;
                        this.filteredListings = searchResults;
                        if (this.filteredListings.length<30){
                            this.retrieveListings();
                        }
                    }
                }
                else if(this.following){
                    const searchResults = this.filteredRecentlyAdded.filter((listing) => {
                        const drinkCategory = listing["typeCategory"].toLowerCase();
                        return drinkCategory.includes(drinkCategorySearch);
                    });
                    if (searchResults.length==0 || searchResults==null) {
                        this.errorFound = true;
                        this.errorMessage = 'No results found, please try again.';
                        this.filteredRecentlyAdded = [];
                        this.retrieveListings();
                    } 
                    else {
                        this.errorFound = false;
                        this.errorMessage = '';
                        this.filteredRecentlyAdded = searchResults;
                        if(this.filteredRecentlyAdded.length<30){
                            this.retrieveListings();
                        }
                    }
                }
            },

            clearSelection() {
                // Handle the click event here
                this.resetListings()
                this.selectedDrinkType = ''
                this.selectedCategory = ''
                this.isFilterType = ''
                if(this.discovery){
                    this.mostReviews=[]
                    this.getMostReviews()
                }
            },

            clearCategory() {
                // Handle the click event here
                this.resetListings()
                this.selectDrinkType(this.selectedDrinkType)
                this.moreListings=true
            },

            // check if user has already added listing to shelf, add colour to button accordingly
            checkDrinkLists(listing) {
                const haveTried = this.drinkList.haveTried.includes(listing.listingName);
                const wantToTry = this.drinkList.wantToTry.includes(listing.listingName);

                const haveTriedButton = `
                <button type="button" class="btn custom-drink-list-btn rounded-0 ${haveTried ? 'disabled' : ''}">
                    Have tried
                </button>
                `;

                const wantToTryButton = `
                <button type="button" class="btn custom-drink-list-btn rounded-0 ${wantToTry ? 'disabled' : ''}">
                    Want to try
                </button>
                `;

                return {
                    buttons: {
                        haveTried: haveTriedButton,
                        wantToTry: wantToTryButton,
                    }
                }
            },

            // find drink name given reviewTarget
            findDrinkNameForReview(reviewTarget) {
                if (reviewTarget) {
                    let drink = this.listings.find(listing => listing.id == reviewTarget);
                    if (drink) {
                        let drink_name = drink.listingName; 
                        return drink_name;
                    }
                }

                return '';
            },

            // change status of discovery
            changeDiscoveryStatus() {
                if (!this.discovery) {
                    this.discovery = true;
                    this.moreListings = true;
                } 
                if (this.following) {
                    this.following = false;
                }
                this.clearSelection()
            },

            // change status of following
            changeFollowingStatus() {
                if (!this.following) {
                    this.following = true;
                    this.moreListings = true;
                } 
                if (this.discovery) {
                    this.discovery = false;
                }
                this.clearSelection()
            },

            // find drink name given listing
            findDrinkNameForListing(listing) {
                let drink_name = listing.listingName;
                return drink_name;
            },

            // get all reviews that a producer has
            getAllReviews() {
                const reviewCounts = {};
                // Iterate through all reviews
                this.reviews.forEach(review => {
                    const reviewTargetName = this.findDrinkNameForReview(review.reviewTarget);
                    // Check if reviewTargetId is already in reviewCounts
                    if (reviewTargetName in reviewCounts) {
                        reviewCounts[reviewTargetName]++;
                    } else {
                        reviewCounts[reviewTargetName] = 1;
                    }
                });

                // Iterate through all drinks
                this.listings.forEach(drink => {
                    const drinkName = drink.listingName;
                    // Check if drinkId is not in reviewCounts
                    if (! (drinkName in reviewCounts)) {
                        reviewCounts[drinkName] = 0;
                    }
                });

                this.allReviews = reviewCounts;
            },
            
            // get top 5 most reviewed items by producer
            getMostReviews() {
                this.mostReviews = []
                let mostProducerReviews = Object.keys(this.allReviews).sort((a, b) => {
                    return this.allReviews[b] - this.allReviews[a];
                }) // to get top five, add .slice(0, 5)
                mostProducerReviews.forEach(drink => {
                    let review = this.getListingByName(drink);
                    if(review && review !=''){
                        this.mostReviews.push(review);
                    }
                });
            },

            // get listing by name
            getListingByName(name) {
                let listing = this.listings.find(listing => {
                    return listing.listingName == name;
                });
                return listing;
            },

            // get latest review from any users that the current user is following
            async getUsersLatestReviews() {

                // Get the list of users that the current user is following
                let user_ids = this.user.followLists.users.join(",");

                try {
                    const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getReviewsByUserIds?user_ids=${user_ids}`);
                    this.latestReviews = response.data.data;
                }
                catch (error) {
                    console.error(error);
                    this.latestReviews = [];
                }
            },

            // get producers that user follows
            getFollowedProducers() {
                this.followedProducers = this.user.followLists.producers;
            },

            // get listings by producer
            getListingsByProducer() {
                this.followedProducers.forEach(producer => {
                    const producerListings = this.listings.filter(listing => listing.producerID == parseInt(producer));
                    this.allProducerDrinks.push(...producerListings);
                });
            },

            // get venues that user follows
            getFollowedVenues() {
                if (this.user) {
                    this.followedVenues = this.user.followLists.venues;
                }
            },

            // get listings by venue
            getListingsByVenue() {
                this.followedVenues.forEach(venue => {
                    const venueID = parseInt(venue);
                    const venueObject = this.venues.find(v => v.id === venueID);
                    let allMenuItems = venueObject["menu"]
                    let allSectionMenus = allMenuItems.reduce((acc, menuItem) => {
                        return acc.concat(menuItem.sectionMenu);
                    }, []);

                    let allListingsIDs = allSectionMenus.reduce((acc, menuItem) => {
                        return acc.concat(menuItem.itemID); 
                    }, []);

                    let uniqueListingsIDs = [...new Set(allListingsIDs.map(item => item))];
                    let allVenueDrinks = this.listings.filter(listing => {
                        let listing_id = listing.id;
                        return uniqueListingsIDs.includes(listing_id);
                    }).map(listing => ({ ...listing }));
                    this.allVenueDrinks = allVenueDrinks;
                });
            },

            // get recently added
            getRecentlyAdded() {
                this.recentlyAdded = [...new Map(this.allProducerDrinks.concat(this.allVenueDrinks).map(item => [item.id, item])).values()];
            },

            getQuestionsUpdates() {
                // get all following producers updates
                const producerUpdates = this.producers
                    .filter(producer => JSON.stringify(this.followedProducers).includes(JSON.stringify(producer.id)))
                    .reduce((arr, producer) => {
                        if (producer.updates && producer.updates.length > 0) {
                            let updatesWithProducerName = producer.updates.map(update => ({
                                ...update,
                                name: producer.producerName, 
                                id: producer.id,
                                photo: producer.photo,
                                type: 'producerUpdate'
                            }));
                            arr.push(...updatesWithProducerName);
                        }
                        return arr;
                    }, []);

                // get all following venues updates
                const venueUpdates = this.venues
                    .filter(venue => JSON.stringify(this.followedVenues).includes(JSON.stringify(venue.id)))
                    .reduce((arr, venue) => {
                        if (venue.updates && venue.updates.length > 0) {
                            let updatesWithVenueName = venue.updates.map(update => ({
                                ...update,
                                name: venue.venueName, 
                                id: venue.id,
                                photo: venue.photo,
                                type: 'venueUpdate'
                            }));
                            arr.push(...updatesWithVenueName);
                        }
                        return arr;
                    }, []);

                // get all following producers questions with answers
                const producerQuestions = this.producers
                    .filter(producer => JSON.stringify(this.followedProducers).includes(JSON.stringify(producer.id)))
                    .reduce((arr, producer) => {
                        if (producer.questionsAnswers && producer.questionsAnswers.some(qa => qa.answer)) {
                            let questionsWithProducerName = producer.questionsAnswers.map(question => ({
                                ...question,
                                name: producer.producerName, 
                                type: 'producerQuestion'
                            }));
                            arr.push(...questionsWithProducerName);
                        }
                        return arr;
                    }, []);
                // get all following venues questions with answers
                const venueQuestions = this.venues
                    .filter(venue => JSON.stringify(this.followedVenues).includes(JSON.stringify(venue.id)))
                    .reduce((arr, venue) => {
                        if (venue.questionsAnswers && venue.questionsAnswers.some(qa => qa.answer)) {
                            let questionsWithVenueName = venue.questionsAnswers.map(question => ({
                                ...question,
                                name: venue.venueName, 
                                type: 'venueQuestion'
                            }));
                            arr.push(...questionsWithVenueName);
                        }
                        return arr;
                    }, []);

                this.questionsUpdates = [...producerUpdates, ...venueUpdates, ...producerQuestions, ...venueQuestions];
                
                // TO REMOVE after date is added to question answers
                // this.questionsUpdates = [...producerUpdates, ...venueUpdates];

                // sort by date
                this.questionsUpdates.sort((a, b) => {
                    return new Date(b.date) - new Date(a.date);
                });

            
            }, 

            // get time difference
            getTimeDifference(date) {
                let currentDate = new Date();
                let updateDate = new Date(date);
                let timeDifference = currentDate - updateDate;
                let seconds = Math.floor(timeDifference / 1000);
                let minutes = Math.floor(seconds / 60);
                let hours = Math.floor(minutes / 60);
                let days = Math.floor(hours / 24);
                let months = Math.floor(days / 30);
                let years = Math.floor(months / 12);
                if (years > 0) {
                    return years + (years === 1 ? ' year ago' : ' years ago');
                } else if (months > 0) {
                    return months + (months === 1 ? ' month ago' : ' months ago');
                } else if (days > 0) {
                    return days + (days === 1 ? ' day ago' : ' days ago');
                } else if (hours > 0) {
                    return hours + (hours === 1 ? ' hour ago' : ' hours ago');
                } else if (minutes > 0) {
                    return minutes + (minutes === 1 ? ' minute ago' : ' minutes ago');
                } else {
                    return seconds + (seconds === 1 ? ' second ago' : ' seconds ago');
                }
            }, 

            // for bookmark component
            handleIconClick(data) {
                this.bookmarkListingID = data
            },

            async retrieveListings(){
                // if selectedDrinkType not empty, meaning listings are filtered, retrieve based off the drink type and/or drink category
                if(this.discovery){
                    if(this.selectedDrinkType != ''){
                        let lastFilteredId = 0
                        if(this.filteredListings.length>0){
                            lastFilteredId = this.filteredListings[this.filteredListings.length-1].id
                        }
                        let params = {
                            "drinkType" : this.selectedDrinkType.drinkType,
                            "drinkCategory": this.selectedCategory
                        }
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getFiltered30` + '/' + lastFilteredId, { params });
                        this.filteredListings.push(...response.data);
                        if(response.data.length == 0){
                            this.moreListings = false
                        }
                    }
                    // if not, meaning listings are not filtered, retrieve next 30 listings in DB
                    else{
                        let lastId = this.listings[this.listings.length-1].id
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getNext30` + '/' + lastId);
                        this.listings.push(...response.data);
                        if(response.data.length == 0){
                            this.moreListings = false
                        }
                    }
                }
                //Lazy loading for following tab
                else{
                    // TODO: Add in lazy loading filter options, right now just pulling normally
                    // if selectedDrinkType not empty, meaning listings are filtered, retrieve based off the drink type and/or drink category based off following list
                    // if(this.selectedDrinkType!=''){
                    // if not, meaning listings are not filtered, retrieve next 30 listings in DB based off following list
                    // }else{
                        let lastFollowingId = this.recentlyAdded[this.recentlyAdded.length-1].id
                        
                        let params = {
                            "followedProducers" : this.followedProducers,
                            "followedVenues": this.followedVenues.length>this.followCount?this.followedVenues[this.followCount]:'null'
                        }
                        let queryString = new URLSearchParams({
                            followedProducers: JSON.stringify(params.followedProducers),
                            followedVenues: JSON.stringify(params.followedVenues)
                        }).toString();
                        const response = await this.$axios.get(`${process.env.VUE_APP_API_URL}/getData/getNextFollowing30` + '/' + lastFollowingId+ `?${queryString}` );
                        const newItems = response.data.filter(item => !this.recentlyAdded.some(existingItem => existingItem.id === item.id));
                        this.recentlyAdded.push(...newItems);
                        if(response.data.length == 0){
                            this.moreListings = false
                        }
                    // }

                    this.followCount++;
                }
            }

        }
    };
</script>


